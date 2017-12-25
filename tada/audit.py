"""Suppport audit records.  There are two flavors.  One is in
sqllite DB on each valley machine.  One is via MARS service (a
composite of all domes and valleys).

Insure: Everything Submitted is Audited
("Submitted" includes Direct Submit and copied to Dropbox)

DECISION via Slack on 12/15/2017 (Sean, Steve):
  "If TADA fails to audit, it should abort ingest."
"""

import logging
import sqlite3
import datetime
import hashlib
#import urllib.request
#import json
import requests
import os.path
import socket

from . import ingest_decoder as dec
from . import utils as tut
from . import settings

#!def md5(fname):
#!    hash_md5 = hashlib.md5()
#!    with open(fname, "rb") as f:
#!        for chunk in iter(lambda: f.read(4096), b""):
#!            hash_md5.update(chunk)
#!    return hash_md5.hexdigest()



class Auditor():
    "Maintain audit records both locally (valley) and via MARS service"
    
    def __init__(self):
        self.con = sqlite3.connect('/var/log/tada/audit.db')
        #!self.timeout = (6.05, 7) # (connect, read) in seconds
        self.timeout = 12 
        self.mars_port = settings.mars_port
        self.mars_host = settings.mars_host
        #self.do_svc = settings.do_audit
        #!self.fstops = set(['dome',
        #!                   'mountain:dropbox',
        #!                   'mountain:queue',
        #!                   'mountain:cache',
        #!                   'mountain:anticache',
        #!                   'valley:dropbox',
        #!                   'valley:queue',
        #!                   'valley:cache',
        #!                   'valley:anticache',
        #!                   'archive'])

    def set_fstop(self, md5sum, fstop, host=None):
        """Update audit service with hhe most downstream stop of FITS file"""
        if host == '' or host == None:
            host = socket.getfqdn() # this host
        logging.debug('AUDIT.set_fstop({}, {}, {})'.format(md5sum, fstop, host))
        uri = ('http://{}:{}/audit/fstop/{}/{}/{}/'
               .format(self.mars_host, self.mars_port, md5sum, fstop, host))

        machine = fstop.split(':')[0]
        logging.debug('DBG-0: fstop uri={}'.format(uri))
        try:
            response = requests.post(uri, timeout=self.timeout)
            logging.debug('DBG-2: uri={}, response={}'.format(uri, response))
            #return response.text
        except  Exception as err:
            logging.error('AUDIT: fstop Error contacting service via "{}"; {}'
                          .format(uri, str(err)))
            return False
        return True


    def log_audit(self, md5sum, origfname, success, archfile, err,
                  orighdr=None, newhdr=None):
        """Log audit record to MARS.
        origfname:: absolute dome filename
        md5sum:: checksum of dome file
        success:: True, False, None; True iff ingest succeeded
        archfile:: base filename of file in archive (if ingested)
        orighdr:: dict; orginal FITS header field/values
        newhdr:: dict; modified FITS header field/values
        """

        if orighdr == None: orighdr = dict()
        if newhdr == None: newhdr = dict()

        try:
            archerr = str(err)
            logging.debug(('log_audit({}, {},{},{},{},'
                           'orighdr={} newhdr={})')
                          .format(md5sum, origfname, success,
                                  archfile, archerr,
                                  orighdr, newhdr))

            now = datetime.datetime.now().isoformat()
            today = datetime.date.today().isoformat()
            obsday = newhdr.get('DTCALDAT', orighdr.get('DTCALDAT', today))
            if ('DTCALDAT' not in newhdr) and ('DTCALDAT' not in orighdr):
                logging.info(('Could not find DTCALDAT in newhdr,orighdr of {},'
                              ' using TODAY as observation day.')
                             .format(origfname))
            tele = newhdr.get('DTTELESC', orighdr.get('DTTELESC', 'UNKNOWN'))
            instrum = newhdr.get('DTINSTRU', orighdr.get('DTINSTRU', 'UNKNOWN'))
            recdic = dict(md5sum=md5sum,
                          # obsday,telescope,instrument; provided by dome
                          #    unless dome never created audit record, OR
                          #    prep error prevented creating new header
                          obsday=obsday,
                          telescope=tele.lower(),
                          instrument=instrum.lower(),
                          #
                          srcpath=origfname,
                          updated=now, # was "recorded"
                          #
                          submitted=now,
                          success=success,
                          archerr=archerr,
                          errcode=dec.errcode(archerr),
                          archfile=os.path.basename(archfile),
                          metadata=orighdr)
            logging.debug('log_audit: recdic={}'.format(recdic))
            logging.info('log_audit: SUCCESS={success}, SRCPATH={srcpath}'
                         .format(**recdic))
            try:
                self.update_local(recdic)
            except Exception as ex:
                logging.error('Could not update local audit.db; {}'.format(ex))

            #!logging.debug('Update audit via service')
            try:
                self.update_svc(recdic)
            except Exception as ex:
                logging.error('Could not update audit record; {}'.format(ex))
            else:
                logging.debug('Updated audit')
        except Exception as ex:
            logging.error('auditor.log_audit() failed: {}'.format(ex))
        logging.debug('DONE: log_audit')
        
    # FIRST something like: sqlite3 audit.db < sql/audit-schema.sql
    def update_local(self, recdic):
        "Add audit record to local sqlite DB. (in case service is down)"
        logging.debug('update_local ({})'.format(recdic,))
        fnames = ['md5sum',
                  'obsday', 'telescope', 'instrument',
                  'srcpath',
                  'updated', #'recorded',
                  'submitted',
                  'success',  'archerr', 'archfile',   ]
        values = [recdic[k] for k in fnames]
        lut = dict(updated='recorded') # rename fields
        fnames = [lut.get(k,k) for k in fnames]
        
        #! logging.debug('update_local ({}) = {}'.format(fnames,values))
        # replace the non-primary key values with new values.
        sql = ('INSERT OR REPLACE INTO audit ({}) VALUES ({})'
               .format(','.join(fnames),
                       (('?,' * len(fnames))[:-1])))
        self.con.execute(sql, tuple(values))
        self.con.commit()
    
    def update_svc(self, recdic):
        """Add audit record to svc."""
        if self.mars_host == None or self.mars_port == None:
            logging.error('Missing AUDIT host ({}) or port ({}).'
                          .format(self.mars_host, self.mars_port))
            return False
        uri = 'http://{}:{}/audit/update/'.format(self.mars_host, self.mars_port)
        fnames = ['md5sum',
                  'obsday', 'telescope', 'instrument',
                  'srcpath', 'updated', 'submitted',
                  'success', 'archerr', 'errcode', 'archfile',
                  # 'metadata',
        ]
        ddict = dict()
        for k in fnames:
            ddict[k] = recdic[k]
        logging.debug('Updating audit record via {}; json={}'
                      .format(uri, ddict))
        try:
            req = requests.post(uri, json=ddict, timeout=self.timeout)
            logging.debug('auditor.update_svc: response={}, status={}, json={}'
                          .format(req.text, req.status_code, ddict))
            req.raise_for_status()
            #return req.text
        except  Exception as err:
            logging.error('MARS audit svc "{}"; {}; {}; json={}'
                          .format(uri, req.text, str(err), ddict))
            return False
        logging.debug('DONE: Adding audit record')
        return True

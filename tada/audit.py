"""Suppport audit records.  There are two flavors.  One is in
sqllite DB on each valley machine.  One is via MARS service (a
composite of all domes and valleys).
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

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()



class Auditor():
    "Maintain audit records both locally (valley) and via MARS service"
    
    def __init__(self):
        cfg = tut.read_hiera_yaml()
        self.con = sqlite3.connect('/var/log/tada/audit.db')
        self.timeout = (3.05, 5) # (connect, read) in seconds
        self.mars_port = cfg['mars_port']
        self.mars_host = cfg['mars_host']
        self.do_svc = cfg.get('do_audit',True)
        
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
        if not self.do_svc:
            return False
        if host == None:
            host = socket.getfqdn() # this host
        logging.debug('AUDIT.set_fstop({}, {}, {})'.format(md5sum, fstop, host))
        uri = ('http://{}:{}/audit/fstop/{}/{}/{}/'
               .format(self.mars_host, self.mars_port, md5sum, fstop, host))

        logging.debug('DBG-0: fstop uri={}'.format(uri))
        #!ddict = dict(md5sum=md5sum, fstop=fstop)
        #!machine = fstop.split(':')[0]
        #!if machine == 'dome':
        #!    ddict['dome_host'] = dome_host
        #!elif machine == 'mountain':
        #!    ddict['mountain_host'] = mtn_host
        #!elif machine == 'valley':
        #!    ddict['valley_host'] = val_host
        try:
            response = requests.post(uri, timeout=self.timeout)
            logging.debug('DBG-2: uri={}, response={}'.format(uri,response))
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
        md5sum]:: checksum of dome file
        success:: True, False, None; True iff ingest succeeded
        archfile:: base filename of file in archive (if ingested)
        orighdr:: dict; orginal FITS header field/values
        newhdr:: dict; modified FITS header field/values
        """

        if orighdr == None: orighdr = dict()
        if newhdr == None: newhdr = dict()

        try:
            #!origfname = prms.get('filename','filename-NA-in-yaml')
            #!md5sum = prms.get('md5sum', 'md5sum-NA-in-yaml')
            #!if ('filename' in prms) and ('md5sum' not in prms):
            #!    # We have a file but no md5sum
            #!    md5sum = md5(prms['filename'])
            #~ if md5sum == None:  md5sum = md5(origfname)
            archerr = str(err)

            logging.debug('log_audit({}, {},{},{},{},{},{} do_svc={})'
                          .format(md5sum, origfname, success,
                                  archfile, archerr,
                                  orighdr, newhdr, self.do_svc))
            #!if not success:
            #!    logging.error('log_audit; archive ingest error: {}'
            #!                  .format(archerr))

            now = datetime.datetime.now().isoformat()
            today = datetime.date.today().isoformat()

            obsday = newhdr.get('DTCALDAT',orighdr.get('DTCALDAT', today))
            if ('DTCALDAT' not in newhdr) and ('DTCALDAT' not in orighdr):
                logging.info(('Could not find DTCALDAT in orighdr of {},'
                              ' using TODAY as observation day.')
                             .format(origfname))
            tele = newhdr.get('DTTELESC',orighdr.get('DTTELESC', 'unknown'))
            instrum = newhdr.get('DTINSTRU',orighdr.get('DTINSTRU', 'unknown'))
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
            try:
                self.update_local(recdic)
            except Exception as ex:
                logging.error('Could not update local audit.db; {}'.format(ex))

            if self.do_svc:
                logging.debug('Update audit via service')
                try:
                    self.update_svc(recdic)
                except Exception as ex:
                    logging.error('Could not update remote audit record; {}'.format(ex))
            else:
                logging.debug('Did not update via audit service')
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
                  'metadata',
        ]
        ddict = dict()
        for k in fnames:
            ddict[k] = recdic[k]
        logging.debug('Adding audit record via {}; json={}'.format(uri, ddict))
        try:
            req = requests.post(uri, json=ddict, timeout=self.timeout)
            #logging.debug('auditor.update_svc: response={}'.format(req.text))
            #return req.text
        except  Exception as err:
            logging.error('AUDIT: Error contacting service via "{}"; {}'
                          .format(uri, str(err)))
            return False
        logging.debug('DONE: Adding audit record')
        return True



        




"""Suppport audit records via MARS service (a
composite of all domes and valleys).

Insure: Everything Submitted is Audited
("Submitted" includes Direct Submit and copied to Dropbox)

DECISION via Slack on 12/15/2017 (Sean, Steve):
  "If TADA fails to audit, it should abort ingest."
"""

import logging
import datetime
import hashlib
import requests
import os.path
import socket

#from . import ingest_decoder as dec
from . import utils as tut
from . import tada_settings as ts
import tada.errorcoding as ec

class Auditor():
    "Maintain audit records both locally (valley) and via MARS service"
    
    def __init__(self):
        #!self.timeout = (6.05, 7) # (connect, read) in seconds
        self.timeout = 12 
        self.natica_port = ts.natica_port
        self.natica_host = ts.natica_host
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
               .format(self.natica_host, self.natica_port, md5sum, fstop, host))

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


    def log_audit(self, md5sum, origfname, success, archfile, reason,
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
            assert isinstance(reason, str)
            logging.debug(('log_audit(md5={}, origfn={},success={},archfn={},err={},'
                           'orighdr={} newhdr={})')
                          .format(md5sum, origfname, success,
                                  archfile, reason,
                                  orighdr, newhdr))

            now = datetime.datetime.now().isoformat()
            #! today = datetime.date.today().isoformat()
            #! obsday = newhdr.get('DTCALDAT', orighdr.get('DTCALDAT', today))
            #! if ('DTCALDAT' not in newhdr) and ('DTCALDAT' not in orighdr):
            #!     logging.info(('Could not find DTCALDAT in newhdr,orighdr of {},'
            #!                   ' using TODAY as observation day.')
            #!                  .format(origfname))

            tele = newhdr.get('DTTELESC', orighdr.get('DTTELESC', 'UNKNOWN'))
            instrum = newhdr.get('DTINSTRU', orighdr.get('DTINSTRU', 'UNKNOWN'))
            errcode = '' if success else ec.code_err(reason)
            reason = '' if success else reason
            recdic = dict(md5sum=md5sum,
                          # obsday,telescope,instrument; provided by dome
                          #    unless dome never created audit record, OR
                          #    prep error prevented creating new header
                          #! obsday=obsday,
                          telescope=tele.lower(),
                          instrument=instrum.lower(),
                          #
                          srcpath=origfname,
                          updated=now, # was "recorded"
                          #
                          submitted=now,
                          success=success,
                          reason=reason,
                          errcode=errcode,
                          archfile=os.path.basename(archfile) if archfile else '',
                          metadata=orighdr)
            logging.debug('log_audit: recdic={}'.format(recdic))
            logging.info('log_audit: SUCCESS={success}, SRCPATH={srcpath}'
                         .format(**recdic))

            #!logging.debug('Update audit via service')
            try:
                self.update_svc(recdic)
            except Exception as ex:
                logging.error('Could not update audit record; {}'.format(ex))
            else:
                logging.debug('Updated audit')
        except Exception as ex:
            logging.exception('auditor.log_audit() failed: {}'.format(ex))
        logging.debug('DONE: log_audit')
        
    
    def update_svc(self, recdic):
        """Add audit record to svc."""
        if self.natica_host == None or self.natica_port == None:
            logging.error('Missing AUDIT host ({}) or port ({}).'
                          .format(self.natica_host, self.natica_port))
            return False
        uri = 'http://{}:{}/audit/update/'.format(self.natica_host,
                                                  self.natica_port)
        fnames = ['md5sum',
                  'obsday', 'telescope', 'instrument',
                  'srcpath', 'updated', 'submitted',
                  'success', 'errcode', 'archfile', 'reason',
                  # 'metadata',
        ]
        ddict = dict()
        for k in fnames:
            if k in recdic:
                ddict[k] = recdic[k]
        logging.debug('Updating audit record via uri={}; ddict={}'
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

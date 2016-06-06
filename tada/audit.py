"""Suppport audit records.  There are two flavors.  One is in
sqllite DB on each valley machine.  One is via MARS service (a
composite of all domes and valleys).
"""

import logging
import sqlite3
import datetime
#import urllib.request
#import json
import hashlib
import requests
import os.path


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

class Auditor():
    "Maintain audit records both locally (valley) and via MARS service"
    
    def __init__(self, mars_host, mars_port, use_service):
        self.con = sqlite3.connect('/var/log/tada/audit.db')
        self.mars_port = mars_port
        self.mars_host = mars_host
        self.do_svc = use_service #if pprms.get('do_audit',False):

    def log_audit(self, localfits, origfname, success, archfile,
                  err, hdr, newhdr):
        try:
            archerr = str(err)
            logging.debug('log_audit({},{},{},{},{},{} do_svc={})'
                          .format(origfname, success, archfile, archerr,
                                  hdr, newhdr, self.do_svc))
            logging.error(archerr)

            now = datetime.datetime.now().isoformat()
            today = datetime.date.today().isoformat()
            if 'DTCALDAT' not in newhdr:
                logging.error('Could not find DTCALDAT in hdr of {}, using TODAY'
                              .format(origfname))
            fields=dict(md5sum=md5(localfits),
                        # obsday,telescope,instrument; provided by dome
                        #    unless dome never created audit record, OR
                        #    prep error prevented creating new header
                        obsday=newhdr.get('DTCALDAT',today),
                        telescope=newhdr.get('DTTELESC','unknown'),
                        instrument=newhdr.get('DTINSTRU','unknown'),
                        #
                        srcpath=origfname,
                        recorded=now, # should match be when DOME created record
                        #
                        submitted=now,
                        success=success,
                        archerr=archerr,
                        archfile=os.path.basename(archfile),
                        metadata=hdr )
            try:
                self.update_local(fields)
            except:
                logging.error('Cound not update local audit.db')

            if self.do_svc:
                logging.debug('Update audit via service')
                try:
                    self.update_svc(fields)
                except:
                    logging.error('Cound not update remote audit record')
            else:
                logging.debug('Did not update via audit service')
        except Exception as ex:
            logging.error('auditor.log_audit() failed: {}'.format(ex))

    # FIRST something like: sqlite3 audit.db < sql/audit-schema.sql
    def update_local(self, fields):
        "Add audit record to local sqlite DB. (in case service is down)"
        fnames = ['md5sum',
                  'obsday', 'telescope', 'instrument',
                  'srcpath', 'recorded', 'submitted',
                  'success',  'archerr', 'archfile',
        ]
        values = [fields[k] for k in fnames]
        logging.debug('update_local ({}) = {}'.format(fnames,values))
        # replace the non-primary key values with new values.
        self.con.execute('INSERT OR REPLACE INTO audit ({}) VALUES ({})'
                         .format(','.join(fnames),  ('?,' * len(fnames))[:-1]),
                         *values)
        self.con.commit()
    
    def update_svc(self, fields):
        """Add audit record to svc."""
        if self.mars_host == None or self.mars_port == None:
            logging.error('Missing AUDIT host ({}) or port ({}).'
                          .format(self.mars_host, self.mars_port))
            return False
        uri = 'http://{}:{}/audit/update/'.format(self.mars_host, self.mars_port)
        fnames = ['md5sum',
                  'obsday', 'telescope', 'instrument',
                  'srcpath', 'recorded', 'submitted',
                  'success', 'archerr', 'archfile',
                  'metadata',
        ]
        ddict = dict()
        for k in fnames:
            ddict[k] = fields[k]
            logging.debug('Adding audit record via {}; json={}'
                          .format(uri, ddict))
        try:
            req = requests.post(uri, json=ddict)
            logging.debug('auditor.update_svc: response={}'.format(req.text))
            return req.text
        except  Exception as err:
            logging.error('AUDIT: Error contacting service via "{}"; {}'
                          .format(uri, str(err)))
            return False
        return True



        




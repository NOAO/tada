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

# FIRST something like: sqlite3 audit.db < sql/audit-schema.sql
con = sqlite3.connect('/var/log/tada/audit.db')
def audit_local(fields):
    "Add audit record to local sqlite DB. (in case service is down)"
    fnames = ['md5sum',
              'obsday', 'telescope', 'instrument',
              'srcpath', 'recorded', 'submitted',
              'success',  'archerr', 'archfile',
              ]
    values = [fields[k] for k in fnames]
    # replace the non-primary key values with new values.
    con.execute('INSERT OR REPLACE INTO audit ({}) VALUES ({})'
                .format(','.join(fnames),  ('?,' * len(fnames))[:-1]),
                values)
    con.commit()
    
def audit_svc(fields,
              #ws_host='payson.tuc.noao.edu',
              ws_host='valley.sdm.noao.edu',
              ws_port=8000, svc_timeout=6):
    """Add audit record to svc."""
    if ws_host == None or ws_port == None:
        logging.error('Missing AUDIT host ({}) or port ({}).'
                      .format(ws_host, ws_port))
        return False
    uri = 'http://{}:{}/audit/update/'.format(ws_host, ws_port)
    fnames = ['md5sum',
              'obsday', 'telescope', 'instrument',
              'srcpath', 'recorded', 'submitted',
              'success', 'archerr', 'archfile',
              'metadata',
              ]
    ddict = dict()
    for k in fnames:
        ddict[k] = fields[k]
    logging.debug('Adding audit record via {}; json={}'.format(uri, ddict))
    try:
        req = requests.post(uri, json=ddict)
        return req.text
    except  Exception as err:
        logging.error('AUDIT: Error contacting service via "{}"; {}'
                      .format(uri, str(err)))
        return False
    return True



def log_audit(origfname, success, archfile, archerr, hdr, newhdr):
    do_audit=True #if pprms.get('do_audit',False):
    logging.debug('log_audit({},{},{},{},{},{} do_audit={})'
                  .format(origfname, success, archfile, archerr, hdr, newhdr,
                          do_audit))
    now = str(datetime.datetime.now())
    fields=dict(md5sum=md5(origfname),
                # obsday,telescope,instrument; provided by dome
                #    unless dome never created audit record, OR
                #    prep error prevented creating new header
	        obsday=newhdr.get('DTCALDAT'),
	        telescope=newhdr.get('DTTELESC','unknown'),
	        instrument=newhdr.get('DTINSTRU','unknown'),
                #
	        srcpath=origfname,
	        recorded=now, # should match be when DOME created record
	        submitted=now,
	        success=success,
	        archerr=archerr,
	        archfile=os.path.basename(archfile),
                metadata=hdr,
                )
    audit_local(fields)

    if do_audit:
        logging.debug('Update audit via service')
        audit_svc(fields)
    else:
        logging.debug('Did not update via audit service')
        




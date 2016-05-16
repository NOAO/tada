"""Suppport audit records.  There are two flavors.  One is in
sqllite DB on each valley machine.  One is via MARS service (a
composite of all domes and valleys).

"""

import logging
import sqlite3
import datetime
import urllib.request
import json
import hashlib

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# FIRST something like: sqlite3 audit.db < sql/audit-schema.sql
con = sqlite3.connect('/var/log/tada/audit.db')

def audit_svc(source_pathname, archive_filename, status, errmsg, metadatadict,
              ws_host='mars.sdm.noao.edu', ws_port=8000, svc_timeout=6):
    """Add audit record to svc."""
    if ws_host == None or ws_port == None:
        logging.error('Missing AUDIT host ({}) or port ({}).'
                      .format(ws_host,ws_port))
        return False
    logging.debug('Adding audit record')
    url = 'http://{}:{}/audit/update'.format(ws_host, ws_port)
    ddict = dict(md5sum = md5(source_pathname),
                 telescope = metadatadict.get('DTTELESC','unknown'),
                 instrument = metadatadict.get('DTINSTRU','unknown'),
                 srcpath = source_pathname,
                 submitted = datetime.datetime.now(),
                 success = status,
                 archerr = errmsg,
                 archfile = archive_filename,
                 metadata = metadatadict,  #updated metadata fields
                 )
    data = bytes(json.dumps(ddict), 'utf-8')
    req = urllib.request.Request(url)
    req.add_header('Content-Type', 'application/json')
    try:
        # INSTEAD, use: https://requests.readthedocs.org/        
        with urllib.request.urlopen(req, data=data, timeout=svc_timeout) as f:
            response = f.read().decode('utf-8')
            #!logging.debug('MARS: server response="{}"'.format(response))
            return response
    except  Exception as err:
        logging.error('AUDIT: Error contacting service via "{}"; {}'
                      .format(url, str(err)))
        return False
    return True


def log_audit(origfname, success, archfile, archerr, hdr,
              do_audit=True):
    logging.debug('log_audit({},{},{},{},{}, do_audit={})'
                  .format(origfname, success, archfile, archerr, hdr,do_audit))
    now = datetime.datetime.now()
    # replace the non-primary key values with new values.
    con.execute('INSERT OR REPLACE INTO audit VALUES (?,?,?,?,?,?,?,?)',
                (hdr.get('DTTELESC','unknown'), # telescope
                 hdr.get('DTINSTRU','unknown'), # instrument
                 origfname,
                 now, # recorded
                 now, # submitted
                 success,
                 archerr,
                 archfile
                ))
    con.commit()
    #if pprms.get('do_audit',False):
    if do_audit:
        logging.debug('Update audit via service')
        audit_svc(origfname, archfile, success, archerr, hdr)
    else:
        logging.debug('Did not update via audit service')
        




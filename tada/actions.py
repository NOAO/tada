"Actions that can be run against entry when popping from  data-queue."
# 2.4.18
import logging
import os
import os.path
import subprocess
import magic
import socket
import shutil
import time
from pathlib import PurePath
import hashlib
import traceback

import dataq.dqutils as du
import dataq.red_utils as ru

from . import submit as tsub
from . import fits_utils as fu
#!from . import diag
#!from . import config
from . import exceptions as tex
from . import utils as tut
from . import audit
from . import tada_settings as ts

auditor = audit.Auditor()



##############################################################################
### Actions
###
###   Form: func(queue_entry_dict[filename,checksum], queuename)
###   RETURN: True iff successful
###           False or exception on error
###

def network_move(rec, qname):
    "Transfer from Mountain to Valley"
    logging.debug('EXECUTING actions.network_move(rec="{}", qname="{}")'
                  .format(rec,qname))
    thishost = socket.getfqdn()
    md5sum = rec['checksum']
    auditor.set_fstop(md5sum, 'mountain:cache', thishost)

    tempfname = rec['filename']  # absolute path (in temp cache)
    fname = tempfname.replace('/cache/.queue/', '/cache/')
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    shutil.move(tempfname,fname) # from temp (non-rsync) dir to rsync dir
    shutil.move(tempfname+'.yaml', fname+'.yaml')
    source_root = '/var/tada/cache' 
    sync_root =  'rsync://tada@{}/cache'.format(ts.valley_host)
    valley_root = '/var/tada/cache'
    popts, pprms = fu.get_options_dict(fname) # .yaml
    if thishost == ts.valley_host:
        logging.error(('Current host ({}) is same as "valley_host" ({}). '
                      'Not moving file!')
                      .format(thishost, ts.valley_host))
        return None


    logging.debug('source_root={}, fname={}'.format(source_root, fname))
    if fname.find(source_root) == -1:
        raise Exception('Filename "{}" does not start with "{}"'
                        .format(fname, source_root))

    # ifname = os.path.join(sync_root, os.path.relpath(fname, source_root))
    # optfname = ifname + ".options"
    newfname = fname # temp dir, not rsync
    out = None
    try:
        # Use feature of rsync 2.6.7 and later that limits path info
        # sent as implied directories.  The "./" marker in the path
        # means "append path after this to destination prefix to get
        # destination path".
        # e.g. '/var/tada/mountain_cache/./pothiers/1294/'
        rsync_source_path = '/'.join([str(PurePath(source_root)),
                                      '.',
                                      str(PurePath(newfname)
                                          .relative_to(source_root).parent),
                                      ''])
        # The directory of newfname is unique (user/jobid)
        # Copy full contents of directory containing newfname to corresponding
        # directory on remote machine (under mountain_mirror).
        cmdline = ['rsync', 
                   '--super',
                   '--perms',    # preserve permissions
                   '--stats',    # give some file-transfer stats
                   ###
                   '--chmod=ugo=rwX',
                   #!'--compress', # we generally fpack fits files
                   '--contimeout=20',
                   '--password-file', '/etc/tada/rsync.pwd',
                   '--recursive',
                   '--relative',
                   '--exclude=".*"',
                   '--remove-source-files', 
                   #sender removes synchronized files (non-dir)
                   '--timeout=40', # seconds
                   #! '--verbose',
                   #! source_root, sync_root]
                   rsync_source_path,
                   sync_root
                   ]
        tic = time.time()
        out = subprocess.check_output(cmdline,
                                      stderr=subprocess.STDOUT)
        logging.debug('rsync completed in {:.2f} seconds'
                      .format(time.time() - tic))
    except Exception as ex:
        logging.warning('Failed to transfer from Mountain to Valley using: {}; '
                        '{}; {}'
                        .format(' '.join(cmdline),
                                ex,
                                out
                            ))
        # Any failure means put back on queue. Keep queue handling
        # outside of actions where possible.
        #! raise
        # Do NOT raise exception since we will re-do rsync next time around
        return False

    # successfully transfered to Valley
    auditor.set_fstop(md5sum, 'valley:cache', ts.valley_host)
    logging.debug('rsync output:{}'.format(out))
    logging.info('Successfully moved file from {} to VALLEY'.format(newfname))
    logging.debug('VALLEY transfer is: {}'.format(sync_root))
    mirror_fname = os.path.join(valley_root,
                                os.path.relpath(newfname, source_root))
    try:
        # What if QUEUE is down?!!!
        ru.push_direct(ts.valley_host, ts.redis_port,
                       mirror_fname, md5sum)
    except Exception as ex:
        logging.error('Failed to push to queue on {}; {}'
                      .format(ts.valley_host, ex))
        logging.error('push_to_q stack: {}'.format(du.trace_str()))
        raise
    auditor.set_fstop(md5sum, 'valley:queue', ts.valley_host)
    return True
    # END network_move

def submit(rec, qname):
    """ACTION done against record popped from dataqueue"""
    logging.debug('EXECUTING actions.submit(rec="{}", qname="{}")'
                  .format(rec,qname))
    ok = False
    fitsfile = rec['filename']
    thishost = socket.getfqdn()
    md5sum = rec['checksum']

    auditor.set_fstop(md5sum, 'valley:cache', thishost)

    try:
        status,jmsg = tsub.submit_to_archive(fitsfile)
        ok = status
        logging.debug('Submit results: status={}, msg={}'.format(status,jmsg))
    except Exception as err:
        msg = ('File ({}) not ingested; {}'.format(fitsfile, err))
        logging.exception(msg)
        ok = False
    auditor.set_fstop(md5sum, 'natica:submit', ts.valley_host)
    logging.debug('DONE actions.submit(rec="{}", qname="{}"); fstop=natica:submit'
                  .format(rec,qname))
    return ok

    

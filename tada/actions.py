"Actions that can be run against entry when popping from  data-queue."
import logging
import os
import os.path
import subprocess
import magic
import shutil
import time
from datetime import datetime
from pathlib import PurePath

#! from . import irods_utils as iu
from . import submit as ts
from . import diag
from . import fits_utils as fu
from . import exceptions as tex
import dataq.dqutils as du
import dataq.red_utils as ru


# +++ Add code here if TADA needs to handle additional types of files!!!
def file_type(filename):
    """Return an abstracted file type string.  MIME isn't always good enough."""
    type = 'UNKNOWN'
    if magic.from_file(filename).decode().find('FITS image data') >= 0:
        type = 'FITS'
    elif magic.from_file(filename).decode().find('JPEG image data') >= 0:
        type = 'JPEG'
    elif magic.from_file(filename).decode().find('script text executable') >= 0:
        type = 'shell script'
    return type
    

##############################################################################

def network_move(rec, qname, **kwargs):
    "Transfer from Mountain to Valley"
    logging.debug('EXECUTING network_move()')
    for p in ['qcfg', 'dirs']:
        if p not in kwargs:
            raise Exception(
                'ERROR: "network_move" Action did not get required '
                +' keyword parameter: "{}" in: {}'
                .format(p, kwargs))
    qcfg=kwargs['qcfg']
    dirs=kwargs['dirs']
    logging.debug('dirs={}'.format(dirs))

    nextq = qcfg[qname]['next_queue']
    dq_host = qcfg[nextq]['dq_host']
    dq_port = qcfg[nextq]['dq_port']
    redis_port = qcfg[nextq]['redis_port']

    source_root = '/var/tada/cache' # qcfg[qname]['cache_dir']
    pre_action = qcfg[qname].get('pre_action',None)
    sync_root =  qcfg[qname]['mirror_dir']
    valley_root = '/var/tada/cache' # qcfg[nextq]['mirror_dir']
    fname = rec['filename']            # absolute path

    logging.debug('source_root={}, fname={}'.format(source_root, fname))
    if fname.find(source_root) == -1:
        raise Exception('Filename "{}" does not start with "{}"'
                        .format(fname, source_root))

    ifname = os.path.join(sync_root, os.path.relpath(fname, source_root))
    optfname = ifname + ".options"    
    newfname = fname
    logging.debug('pre_action={}'.format(pre_action))
    if pre_action:
        # pre_action is full path to shell script to run.
        # WARNING: a bad script could do bad things to the
        #    mountain_cache files!!!
        # Script must accept three params:
        #   1. absolute path of file from queue
        #   2. absolute path mountain_cache
        #   3. absolute path of file containing options
        # Stdout and stderr from pre_action will be logged to INFO.
        # Error (non-zero return code) will be logged to ERROR but normal
        # TADA processing will continue.
        try:
            cmdline = [pre_action, fname, source_root, fname+'.options']
            diag.dbgcmd(cmdline)
            bout = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
            if len(bout) > 0:
                out = bout.decode('utf-8')
                newfname = out.split()[0]
                logging.info('pre_action "{}", newfname={}, output: {}'
                             .format(pre_action, newfname, out))
        except subprocess.CalledProcessError as cpe:
            logging.warning('Failed Transfer pre_action ({} {} {}) {}; {}'
                            .format(pre_action, fname, source_root,
                                    cpe, cpe.output ))
        
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
                   '--remove-source-files',
                   #sender removes synchronized files (non-dir)
                   '--timeout=40', # seconds
                   #! '--verbose',
                   #! source_root, sync_root]
                   rsync_source_path,
                   sync_root
                   ]
        diag.dbgcmd(cmdline)
        tic = time.time()
        out = subprocess.check_output(cmdline,
                                      stderr=subprocess.STDOUT)
        logging.info('rsync completed in {:.2f} seconds'
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
        # raise # Do NOT raise exception since we will re-do rsync next time around
        return False

    # successfully transfered to Valley
    logging.debug('rsync output:{}'.format(out))
    logging.info('Successfully moved file from {} to {}'
                 .format(newfname, sync_root))
    mirror_fname = os.path.join(valley_root,
                                os.path.relpath(newfname, source_root))
    try:
        # What if QUEUE is down?!!!
        #!du.push_to_q(dq_host, dq_port, mirror_fname, rec['checksum'])
        ru.push_direct(dq_host, redis_port,
                       mirror_fname, rec['checksum'],
                       qcfg[nextq])
    except Exception as ex:
        logging.error('Failed to push to queue on {}:{}; {}'
                        .format(dq_host, dq_port, ex ))
        logging.error('push_to_q stack: {}'.format(du.trace_str()))
        raise
    return True


def logsubmit(src, dest, comment, fail=False,
              submitlog='/var/log/tada/submit.manifest'):
    with open(submitlog, mode='a') as f:
        print('{timestamp}\t{status}\t{srcfname}\t{destfname}\t{msg}'
              .format(timestamp=datetime.now().strftime('%m/%d/%y_%H:%M:%S'),
                      status = 'FAILURE' if fail else 'SUCCESS',
                      srcfname=src,
                      destfname=dest,
                      msg=comment),
              file=f)

    
def submit(rec, qname, **kwargs):
    """Try to modify headers and submit FITS to archive. If anything fails 
more than N times, move the queue entry to Inactive. (where N is the 
configuration field: maximum_errors_per_record)
"""
    logging.debug('submit({},{})'.format(rec, qname))
    qcfg = du.get_keyword('qcfg', kwargs)
    dq_host = qcfg[qname]['dq_host']
    dq_port = qcfg[qname]['dq_port']

    noarc_root =  '/var/tada/anticache'   # qcfg[qname]['noarchive_dir']
    mirror_root = '/var/tada/cache'       # qcfg[qname]['mirror_dir']
    #submitlog =  '/var/log/tada/submit.manifest' # qcfg[qname]['submitlog']

    # eg. /tempZone/mountain_mirror/other/vagrant/16/text/plain/fubar.txt
    ifname = rec['filename']            # absolute path (mountain_mirror)
    checksum = rec['checksum']          

    try:
        #! ftype = iu.irods_file_type(ifname)
        ftype = file_type(ifname)
    except Exception as ex:
        logging.error('Execution failed: {}; ifname={}'
                      .format(ex, ifname))
        raise
        
    logging.debug('File type for "{}" is "{}".'
                  .format(ifname, ftype))
    destfname = None
    if 'FITS' == ftype :  # is FITS
        msg = 'FITS_file'
        popts, pprms = fu.get_options_dict(ifname) # .yaml or .options
        origfname = pprms.get('filename',ifname)
        try:
            destfname = ts.submit_to_archive(ifname, checksum, qname, qcfg)
        except Exception as sex:
            msg = 'Failed to submit {}: {}'.format(ifname, sex)
            logsubmit(origfname, ifname, msg, fail=True)
            logging.error(msg)
            return False
            #!raise tex.SubmitException('Failed to submit {}: {}'
            #!                          .format(ifname, sex))
        else:
            msg = 'SUCCESSFUL fits submit; {} as {}'.format(ifname, destfname)
            logging.debug(msg)
            # successfully transfered to Archive
            os.remove(ifname)
            optfname = ifname + ".options"
            logging.debug('Remove possible options file: {}'.format(optfname))
            if os.path.exists(optfname):
                os.remove(optfname)
            logsubmit(origfname, destfname, msg)
    else: # not FITS
        msg = 'non-fits'
        destfname = ifname.replace(mirror_root, noarc_root)
        try:
            os.makedirs(os.path.dirname(destfname), exist_ok=True)
            shutil.move(ifname, destfname)
        except Exception as ex:
            msg = 'Non-FITS file: {}'.format(ex)
            logsubmit(origfname, ifname, msg, fail=True)
            logging.warning('Failed to mv non-fits file from mirror on Valley.')
            raise
        logsubmit(ifname, destfname, 'Non-FITS file')
        # Remove files if noarc_root is taking up too much space (FIFO)!!!
        logging.info('Non-FITS file put in: {}'.format(destfname))
        
    return True
# END submit() action

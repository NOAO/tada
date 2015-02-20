"Actions that can be run against entry when popping from  data-queue."
import logging
import os
import os.path
import subprocess
import magic
import shutil
import time

#! from . import irods_utils as iu
from . import submit as ts
from . import diag

import dataq.dqutils as du

# +++ Add code here if TADA needs to handle additional types of files!!!
def file_type(filename):
    """Return an abstracted file type string.  MIME isn't always good enough."""
    if magic.from_file(filename).decode().find('FITS image data') >= 0:
        return('FITS')
    elif magic.from_file(filename).decode().find('JPEG image data') >= 0:
        return('JPEG')
    elif magic.from_file(filename).decode().find('script text executable') >= 0:
        return('shell script')
    else:
        return('UNKNOWN')
    

##############################################################################

def network_move(rec, qname, **kwargs):
    "Transfer from Mountain to Valley"
    logging.debug('ACTION: network_move()')
    for p in ['qcfg', 'dirs']:
        if p not in kwargs:
            raise Exception(
                'ERROR: "network_move" Action did not get required '
                +' keyword parameter: "{}" in: {}'
                .format(p, kwargs))
    qcfg=kwargs['qcfg']
    dirs=kwargs['dirs']
    logging.debug('dirs={}'.format(dirs))

    nextq = qcfg['transfer']['next_queue']
    dq_host = qcfg[nextq]['dq_host']
    dq_port = qcfg[nextq]['dq_port']

    source_root = qcfg['transfer']['cache_dir']
    sync_root = qcfg['transfer']['mirror_dir']
    valley_root = qcfg['submit']['mirror_dir']
    fname = rec['filename']            # absolute path

    logging.debug('source_root={}, fname={}'.format(source_root, fname))
    if fname.find(source_root) == -1:
        raise Exception('Filename "{}" does not start with "{}"'
                        .format(fname, source_root))

    ifname = os.path.join(sync_root, os.path.relpath(fname, source_root))
    #!ifname = sync_root
    out = None
    try:
        #!iu.irods_put(fname, ifname)
        cmdline = ['rsync',
                   '-rptgo',    #! took out '-az',
                   '--timeout=5',
                   '--contimeout=3',
                   '--remove-source-files',
                   '--stats',
                   '--password-file', '/etc/tada/rsync.pwd',
                   source_root, sync_root]
        diag.dbgcmd(cmdline)
        tic = time.time()
        out = subprocess.check_output(cmdline,
                                      stderr=subprocess.STDOUT)
        logging.debug('rsync complete {:.2f} seconds'.format(time.time() - tic))
    except Exception as ex:
        logging.warning('Failed to transfer from Mountain ({}) to Valley. '
                        '{} => {}; {}'
                        .format(os.getuid(),
                                ex,
                                ex.output.decode('utf-8'),
                                out
                            ))
        # Any failure means put back on queue. Keep queue handling
        # outside of actions where possible.
        raise
    else:
        logging.info('Successfully moved file from {} to {}'
                     .format(fname,sync_root))
        # successfully transfered to Valley
        mirror_fname = os.path.join(valley_root,
                                    os.path.relpath(fname, source_root))
        # What if QUEUE is down?!!!
        du.push_to_q(dq_host, dq_port, mirror_fname, rec['checksum'])
        
        # Files removed by rsync through option '--remove-source-files' above
        #
        #!os.remove(fname)
        #!logging.info('Removed file "{}" from mountain cache'.format(fname))
        #!optfname = fname + ".options"
        #!if os.path.exists(optfname):
        #!    os.remove(optfname)
        #!    logging.debug('Removed options file: {}'.format(optfname))

    return True


def submit(rec, qname, **kwargs):
    """Try to modify headers and submit FITS to archive. If anything fails 
more than N times, move the queue entry to Inactive. (where N is the 
configuration field: maximum_errors_per_record)
"""
    logging.debug('submit({},{})'.format(rec, qname))
    qcfg = du.get_keyword('qcfg', kwargs)
    dq_host = qcfg[qname]['dq_host']
    dq_port = qcfg[qname]['dq_port']

    noarc_root =  qcfg[qname]['noarchive_dir']
    mirror_root =  qcfg[qname]['mirror_dir']

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
    if 'FITS' == ftype :  # is FITS
        try:
            ts.submit_to_archive(ifname, checksum, qname, qcfg)
        except Exception as sex:
            raise sex
        else:
            logging.info('PASSED submit_to_archive({}).'  .format(ifname))
            # successfully transfered to Archive
            os.remove(ifname)
            optfname = ifname + ".options"
            logging.debug('Remove possible options file: {}'  .format(optfname))
            if os.path.exists(optfname):
                os.remove(optfname)
    else: # not FITS
        fname = ifname.replace(mirror_root, noarc_root)
        try:
            os.makedirs(os.path.dirname(fname), exist_ok=True)
            shutil.move(ifname, fname)
        except:
            logging.warning('Failed to mv non-fits file from mirror on Valley.')
            raise
        # Remove files if noarc_root is taking up too much space (FIFO)!!!
        logging.info('Non-FITS file put in: {}'.format(fname))


        
    return True
# END submit() action

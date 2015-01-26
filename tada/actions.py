"Actions that can be run against entry when popping from  data-queue."
import logging
import os
import os.path

import dataq.dqutils as du
from . import irods_utils as iu
from . import submit as ts


def network_move(rec, qname, **kwargs):
    "Transfer from Mountain to Valley"
    import tada.actions
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

    #!irods_root = kwargs['irods_root']  # eg. '/tempZone/'
    source_root = qcfg['transfer']['cache_dir']
    irods_root = qcfg['transfer']['mirror_irods']
    fname = rec['filename']            # absolute path

    logging.debug('source_root={}, fname={}'.format(source_root, fname))
    if fname.index(source_root) != 0:
        raise Exception('Filename "{}" does not start with "{}"'
                        .format(fname, source_root))

    ifname = os.path.join(irods_root, os.path.relpath(fname, source_root))

    try:
        iu.irods_put(fname, ifname)
    except Exception as ex:
        logging.warning('Failed to transfer from Mountain to Valley. {}'
                        .format(ex))
        # Any failure means put back on queue. Keep queue handling
        # outside of actions where possible.
        raise
    else:
        # successfully transfered to Valley
        os.remove(fname)
        logging.info('Removed file "%s" from mountain cache'%(rec['filename'],))
        du.push_to_q(dq_host, dq_port, ifname, rec['checksum'])
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
    irods_root =  qcfg[qname]['mirror_irods'] # '/tempZone/mountain_mirror/'

    # eg. /tempZone/mountain_mirror/other/vagrant/16/text/plain/fubar.txt
    ifname = rec['filename']            # absolute irods path (mtn_mirror)
    checksum = rec['checksum']          
    tail = os.path.relpath(ifname, irods_root) # changing part of path tail

    try:
        ftype = iu.irods_file_type(ifname)
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
    else: # not FITS
        # Put irods file on filesystem. 
        fname = os.path.join(noarc_root, tail)
        try:
            iu.irods_get(fname, ifname, remove_irods=True)
        except:
            logging.warning('Failed to get file from irods on Valley.')
            raise
        # Remove files if noarc_root is taking up too much space (FIFO)!!!
        logging.info('Non-FITS file put in: {}'.format(fname))


    return True
# END submit() action

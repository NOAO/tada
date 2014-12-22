"Dirt needed to submit a fits file to the archive for ingest"
    
import sys
import argparse
import logging
import pyfits
import os, os.path
import socket
import traceback

from . import fits_utils as fu
from . import exceptions as tex
from . import prep_fits_for_ingest as pf
from dataq import dqutils as du
from dataq import irods_utils as iu

# e.g.
# curl "http://nsaserver.pat.sdm.noao.edu:9000/?hdrUri=/noao-tuc-z1/mtn/20141123/kp4m/2013B-0528/kp2066873.hdr"
def http_archive_ingest(hdr_ipath, checksum, qname, qcfg=None):
    """Store ingestible FITS file and hdr in IRODS.  Pass location of hdr to
 Archive Ingest via REST-like interface."""
    logging.debug('EXECUTING: http_archive_ingest({}, {}, {})'
                  .format(hdr_ipath, checksum, qname))

    nsa_host = qcfg[qname]['nsa_host']
    nsa_port = qcfg[qname]['nsa_port']
    irods_host = qcfg[qname]['nsa_irods_host']
    irods_port = qcfg[qname]['nsa_irods_port']
    irods_archive_dir = qcfg[qname]['archive_irods']

    nsaserver_url = ('http://{}:{}/?hdrUri={}'
                     .format(nsa_host, nsa_port, hdr_ipath))
    logging.debug('nsaserver_url = {}'.format(nsaserver_url))

    return False #!!!

    with urllib.requiest.urlopen(nsaserver_url) as f:
        # Only two possible responses are: "Success" or "Failure"
        response = f.readline().decode('utf-8')
    logging.debug('NSA server resonse: = {}'.format(response))
    result = True if response == "Success" else False
    return result
    
def tcp_archive_ingest(fname, checksum, qname, qcfg=None):
    logging.debug('EXECUTING: tcp_archive_ingest({}, {}, {})'
                  .format(fname, qname, qcfg))
    nsa_host = qcfg[qname]['nsa_host']
    nsa_port = qcfg[qname]['nsa_port']
    # register in irods
    # post metadata to archive port

    data = fu.get_archive_header(fname, checksum)
    logging.debug('Prepare to send data over TCP: {}'.format(data))
    
    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
    try:
        logging.debug('Connect to ingest server on {}:{}'
                      .format(nsa_host, nsa_port))
        # Connect to server and send data
        sock.connect((nsa_host, nsa_port))
        sock.sendall(bytes(data + "\n", "utf-8"))

        # Receive data from the server and shut down
        received = str(sock.recv(1024), "utf-8")
    finally:
        sock.close()

    print("Sent:     {}".format(data))
    print("Received: {}".format(received))    

    
def STUB_archive_ingest(fname, qname, qcfg=None):
    'Touch-point for archive ingest. Stub!!!'
    import random #!!! only needed for mockup
    import inspect

    logging.debug('Executing STUB: {}:STUB_archive_ingest()'.format(__file__))
    prop_fail = 0.60
    if random.random() <= prop_fail:  #!!! remove
        logging.debug(
            'Simulated FAILURE [p(Fail)={}] on STUB_archive_ingest({})'
            .format(prop_fail, fname))
        raise Exception(
            'Failed STUB_archive_ingest({}) due to cosmic ray (prob={}).'
            .format(fname, prop_fail))
    else:
        logging.debug(
            'Simulated SUCCESS [p(Fail)={}] on STUB_archive_ingest({})'
            .format(prop_fail, fname))
    return True

# (-sp-) The Archive Ingest process is ugly and the interface is not
# documented (AT ALL, as far as I can tell). It accepts a URI for an
# irods path of a "hdr" for a FITS file. The "hdr" has to be the hdr
# portion of a FITS with 5 lines prepended to it. Its more ugly
# because the submit (HTTP request) may fail but both the hdr and the
# fits irods file location cannot be changed if the submit succeeds.
# But we want them to be a different place if the submit fails. So we
# have to move before the submit, then undo the move if it fails. The
# HTTP response may indicate failure, but I think it could indicate
# success even when there is a failure.  It would make perfect sense
# for the Archive Ingest to read what it needs directly from the FITS
# file (header). It can be done quickly even if the data portion of
# the FITS is large. Not doing so means extra complication and
# additional failure modes.  Worse, because a modified hdr has to be
# sent to Ingest, the actual fits file has to be accessed when
# otherwise we could have just dealt with irods paths. Fortunately,
# the irods icommand "iexecmd" lets us push such dirt to the server.
def submit_to_archive(ifname, checksum, qname, qcfg=None):
    """Ingest a FITS file (really JUST Header) into the archive if
possible.  Ingest involves renaming to satisfy filename
standards. Although I've seen no requirements for it, previous systems
also used a specific 3 level directory structure that is NOT used
here. However the levels are stored in hdr fields SB_DIR{1,2,3}."""
    logging.debug('submit_to_archive({},{})'.format(ifname, qname))
    logging.debug('   qcfg={})'.format(qcfg))
    mirror_idir =  qcfg[qname]['mirror_irods']
    archive_idir =  qcfg[qname]['archive_irods']
    try:
        hdr_ipath = iu.irods_prep_fits_for_ingest(ifname,
                                                  mirror_idir,
                                                  archive_idir)
    except:
        traceback.print_exc()
        raise
    
    try:
        #!STUB_archive_ingest(new_fname, qname, qcfg=qcfg)
        http_archive_ingest(hdr_ipath, checksum, qname, qcfg=qcfg)
    except:
        traceback.print_exc()
        #! logging.debug('Unregister irods {}. Undo the name change: {} => {}'
        #!               .format(iname, new_fname, fname))
        #! iu.irods_unreg(iname)
        #! os.rename(new_fname, fname)
        raise

    return hdr_ipath

def submit(rec, qname, **kwargs):
    """Try to modify headers and submit FITS to archive. If anything fails 
more than N times, move the queue entry to Inactive. (where N is the 
configuration field: maximum_errors_per_record)
"""
    qcfg = du.get_keyword('qcfg', kwargs)
    dq_host = qcfg[qname]['dq_host']
    dq_port = qcfg[qname]['dq_port']

    noarc_root =  qcfg[qname]['noarchive_dir']
    irods_root =  qcfg[qname]['mirror_irods'] # '/tempZone/mountain_mirror/'

    # eg. /tempZone/mountain_mirror/other/vagrant/16/text/plain/fubar.txt
    ifname = rec['filename']            # absolute irods path (mtn_mirror)
    checksum = rec['checksum']          
    tail = os.path.relpath(ifname, irods_root) # changing part of path tail

    ftype = iu.irods_file_type(ifname)
    logging.debug('File type for "{}" is "{}".'
                  .format(ifname, ftype))
    if 'FITS' == ftype :  # is FITS
        try:
            #!fname = submit_to_archive(fname, checksum, qname, qcfg)
            fname = submit_to_archive(ifname, checksum, qname, qcfg)
        except Exception as sex:
            raise sex
        else:
            logging.info('PASSED submit_to_archive({}).'  .format(fname))
    else: # not FITS
        # Put irods file on filesystem. 
        fname = os.path.join(noarc_root, tail)
        try:
            iu.irods_get(fname, ifname)
        except:
            logging.warning('Failed to get file from irods on Valley.')
            raise
        # Remove files if noarc_root is taking up too much space (FIFO)!!!
        logging.info('Non-fits file put in: {}'.format(fname))


    return True
# END submit() action

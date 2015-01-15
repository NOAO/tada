"Dirt needed to submit a fits file to the archive for ingest"
    
import sys
import argparse
import logging
import pyfits
import os, os.path
import socket
import traceback
import tempfile
import pathlib
import urllib

from . import fits_utils as fu
from . import file_naming as fn
from . import exceptions as tex
from . import prep_fits_for_ingest as pf
from dataq import dqutils as du
from dataq import irods_utils as iu

# e.g.
# curl "http://nsaserver.pat.sdm.noao.edu:9000/?hdrUri=/noao-tuc-z1/mtn/20141123/kp4m/2013B-0528/kp2066873.hdr"
def http_archive_ingest(hdr_ipath, checksum, qname, qcfg=None):
    """Store ingestible FITS file and hdr in IRODS.  Pass location of hdr to
 Archive Ingest via REST-like interface."""
    import random # for stubbing random failures (not for production)

    logging.debug('EXECUTING: http_archive_ingest({}, {}, {})'
                  .format(hdr_ipath, checksum, qname))

    nsa_host = qcfg[qname]['nsa_host']
    nsa_port = qcfg[qname]['nsa_port']
    irods_host = qcfg[qname]['nsa_irods_host']
    irods_port = qcfg[qname]['nsa_irods_port']
    irods_archive_dir = qcfg[qname]['archive_irods']
    prob_fail = qcfg[qname]['action_fail_probability']

    nsaserver_url = ('http://{}:{}/?hdrUri={}'
                     .format(nsa_host, nsa_port, hdr_ipath))
    logging.debug('nsaserver_url = {}'.format(nsaserver_url))

    #!logging.warning('http_archive_ingest() using prob_fail= {}'
    #!                .format(prob_fail))
    #!if random.random() <= prob_fail:
    #!    raise tex.SubmitException('Killed by cosmic ray with probability {}'
    #!                              .format(prob_fail))


    with urllib.request.urlopen(nsaserver_url) as f:
        # Only two possible responses are: "Success" or "Failure"
        response = f.readline().decode('utf-8')
    logging.debug('NSA server response: = {}'.format(response))
    result = True if response == "Success" else False
    if not result:
        raise tex.SubmitException('HTTP response from Archive: {}'
                                  .format(response))

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

def prep_for_ingest(mirror_ifname, mirror_idir, archive_idir, archive331):
    """GIVEN: FITS irods path
DO: 
  Augment hdr. 
  Add hdr as text file to irods.
  Copy hdr only across bridge (irods-4 to irods-3 archive_idir)
  Rename FITS to satisfy standards. 
!!! remove from mirror
mirror_ifname :: 
mirror_idir :: from "mirror_irods" in dq_config
archive_idir :: from "archive_irods" in dq_config
archive331 :: from "archive_irods331" in dq_config
RETURN: irods location of hdr file.
    """

    logging.debug('prep_for_ingest: ifname={}, m_dir={}, a_dir={}, a3_dir={}'
                  .format(mirror_ifname, mirror_idir, archive_idir, archive331))

    # Assumes we are running on machine with access to irods physical file!!!
    fname = iu.irods_get_physical(mirror_ifname)
    
    hdr_ifname = "None"
    try:
        # augment hdr (add fields demanded of downstream process)
        hdulist = pyfits.open(fname, mode='update') # modify IN PLACE
        hdr = hdulist[0].header # use only first in list.
        fu.modify_hdr(hdr, fname)

        # Generate standards conforming filename
        new_basename = fn.generate_fname(
            instrument=hdr.get('DTINSTRU', 'NOTA'),
            datetime=hdr['OBSID'],
            obstype=hdr.get('OBSTYPE', 'NOTA'),
            proctype=hdr.get('PROCTYPE', 'NOTA'),
            prodtype=hdr.get('PRODTYPE', 'NOTA'),
            )
        #new_ifname=os.path.join(os.path.dirname(mirror_ifname), new_basename)
        ipath = pathlib.PurePath(mirror_ifname
                                 .replace(mirror_idir, archive_idir))
        new_ipath = ipath.with_name(new_basename)
        new_ifname = str(new_ipath)
        new_ihdr = str(new_ipath.with_suffix('.hdr'))

        # Create hdr as temp file, i-put, delete tmp file (auto on close)
        # Archive requires extra fields prepended to hdr txt! :-<
        with tempfile.NamedTemporaryFile(mode='w') as f:
            ingesthdr = ('#filename = {filename}\n'
                         '#reference = {filename}\n'
                         '#filetype = UNKNOWN\n'
                         '#filesize = {filesize} bytes\n'
                         '#file_md5 = {checksum}\n\n'
                     )
            print(ingesthdr.format(filename=new_basename,
                                   filesize=os.path.getsize(fname),
                                   checksum=iu.get_irods_cksum(mirror_ifname)
                               ),
                  file=f)
            hdr.totextfile(f)
            
            # The only reason we do this is to satisfy Archive Ingest!!!
            # Since it has to have a reference to the FITS file anyhow,
            # Archive Ingest SHOULD deal with the hdr.
            iu.irods_put(f.name, new_ihdr)
            logging.debug('iput new_ihdr to: {}'.format(new_ihdr))
    except:
        raise
    finally: 
        hdulist.flush()
        hdulist.close()
        
    # We might need to change subdirectory name too!!!
    # (but there has been no stated Requirement for subdir structure)
    #   <root>/<SB_DIR1>/<SB_DIR2>/<SB_DIR3>/<base.fits>
    iu.irods_mv_tree(mirror_ifname, new_ifname) # rename FITS

    #
    # At this point both FITS and HDR are in archive_idir
    #

    # Copy both FITS and HDR to legacy iRODS 3.3.1 server that Archive uses
    ihdr331 = new_ihdr.replace(archive_idir, archive331)
    iu.bridge_copy(new_ihdr, ihdr331, remove_orig=True)
    ifname331 = new_ifname.replace(archive_idir, archive331)
    iu.bridge_copy(new_ifname, ifname331, remove_orig=True)

    logging.debug('prep_for_ingest: RETURN={}'.format(ihdr331))
    return ihdr331

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
    #! logging.debug('   qcfg={})'.format(qcfg))
    mirror_idir =  qcfg[qname]['mirror_irods']
    archive_idir =  qcfg[qname]['archive_irods']
    archive331 =  qcfg[qname]['archive_irods331']
    try:
        #!ihdr = iu.irods_prep_fits_for_ingest(ifname, mirror_idir,archive_idir)
        ihdr = prep_for_ingest(ifname, mirror_idir, archive_idir, archive331)
    except:
        #! traceback.print_exc()
        raise
    
    try:
        #!STUB_archive_ingest(new_fname, qname, qcfg=qcfg)
        http_archive_ingest(ihdr, checksum, qname, qcfg=qcfg)
    except:
        #! traceback.print_exc()
        raise

    return ihdr

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
            submit_to_archive(ifname, checksum, qname, qcfg)
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

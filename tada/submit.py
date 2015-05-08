"Dirt needed to submit a fits file to the archive for ingest"
    
import sys
import argparse
import logging
import astropy.io.fits as pyfits
import os
import os.path
import socket
import traceback
import tempfile
import pathlib
import urllib.request
import datetime
from copy import copy

from . import fits_utils as fu
from . import file_naming as fn
from . import exceptions as tex
from . import irods331 as iu
from . import ingest_decoder as idec
 

def http_archive_ingest(hdr_ipath, checksum, qname, qcfg=None):
    """Store ingestible FITS file and hdr in IRODS.  Pass location of hdr to
 Archive Ingest via REST-like interface."""
    import random # for stubbing random failures (not for production)

    logging.debug('EXECUTING: http_archive_ingest({}, {}, {})'
                  .format(hdr_ipath, checksum, qname))

    arch_host = qcfg[qname]['arch_host']
    arch_port = qcfg[qname]['arch_port']
    irods_host = qcfg[qname]['arch_irods_host']
    irods_port = qcfg[qname]['arch_irods_port']
    prob_fail = qcfg[qname]['action_fail_probability']

    archserver_url = ('http://{}:{}/?hdrUri={}'
                     .format(arch_host, arch_port, hdr_ipath))
    logging.debug('archserver_url = {}'.format(archserver_url))


    
    if qcfg[qname].get('disable_archive_svc',0) > 0:
        logging.warning('Ingest DISABLED. '
                        'http_archive_ingest() using prob_fail= {}'
                        .format(prob_fail))
        result = True
        if random.random() <= prob_fail:
            raise tex.SubmitException(
                'Killed by cosmic ray with probability {}'
                .format(prob_fail))
    else:
        result = True
        response = ''
        try:
            with urllib.request.urlopen(archserver_url) as f:
                # As of 1/15/2015 the only two possible responses are:
                #   "Success" or "Failure"
                response = f.readline().decode('utf-8')
            logging.debug('ARCH server response: = {}'.format(response))
            result = True if response == "Success" else False
        except:
            raise
        if not result:
            operator_msg = idec.decodeIngest(response)
            raise tex.SubmitException(
                'HTTP response from Archive Ingest: "{}"; {}'
                .format(response, operator_msg))

    return result
    
def tcp_archive_ingest(fname, checksum, qname, qcfg=None):
    logging.debug('EXECUTING: tcp_archive_ingest({}, {}, {})'
                  .format(fname, qname, qcfg))
    arch_host = qcfg[qname]['arch_host']
    arch_port = qcfg[qname]['arch_port']
    # register in irods
    # post metadata to archive port

    data = fu.get_archive_header(fname, checksum)
    logging.debug('Prepare to send data over TCP: {}'.format(data))
    
    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
    try:
        logging.debug('Connect to ingest server on {}:{}'
                      .format(arch_host, arch_port))
        # Connect to server and send data
        sock.connect((arch_host, arch_port))
        sock.sendall(bytes(data + "\n", "utf-8"))

        # Receive data from the server and shut down
        received = str(sock.recv(1024), "utf-8")
    finally:
        sock.close()

    print("Sent:     {}".format(data))
    print("Received: {}".format(received))    

    

def prep_for_ingest(mirror_fname, mirror_dir, archive331):
    """GIVEN: FITS absolute path
DO: 
  Augment hdr. 
  Add hdr as text file to irods331.
  Rename FITS to satisfy standards. 
  Add fits to irods331
  remove from mirror

mirror_fname :: Mountain mirror on valley
mirror_dir :: from "mirror_dir" in dq_config
archive331 :: from "archive_irods331" in dq_config
RETURN: irods location of hdr file.
    """

    logging.debug('prep_for_ingest: fname={}, m_dir={}, a_dir={}'
                  .format(mirror_fname, mirror_dir, archive331))

    # Name/values passed on LPR command line.
    #   e.g. lpr -P astro -o _INSTRUME=KOSMOS  -o _OBSERVAT=KPNO  foo.fits
    # Only use options starting with '_' and remove '_' from dict key.
    # +++ Add code here to handle other kinds of options passed from LPR.
    optfname = mirror_fname + ".options"
    optstr = ''
    if os.path.exists(optfname):
        with open(optfname,encoding='utf-8') as f:
            optstr = f.readline()
    options = dict([s[1:].split('=') for s in optstr.split() if s[0]=='_'])

    opt_params = dict()  # under-under params. Passed like: lp -d astro -o __x=3
    for k,v in list(options.items()):
        if k[0] =='_':
            opt_params[k[1:]] = v.replace('_', ' ')
            options.pop(k)
    # +++ API: under-under parameters via lp options
    warn_unknown = opt_params.get('warn_unknown', False)
    jidt = opt_params.get('jobid_type',None)  
    source = opt_params.get('source',None)

    #!logging.debug('Options in prep_for_ingest: {}'.format(options))
    logging.debug('Params in prep_for_ingest: {}'.format(opt_params))

    hdr_ifname = "None"
    try:
        # augment hdr (add fields demanded of downstream process)
        logging.debug('Open FITS for hdr update: {}'.format(mirror_fname))
        hdulist = pyfits.open(mirror_fname, mode='update') # modify IN PLACE
        hdr = hdulist[0].header # use only first in list.
        fname_fields = fu.modify_hdr(hdr, mirror_fname, options)
        # Generate standards conforming filename
        # EXCEPT: add field when JIDT given.
        if jidt == 'plain':
            jobid = pathlib.PurePath(mirror_fname).parts[-2]
        elif jidt == 'seconds':
            # hundredths of a second sin 1/1/2015
            jobid = str(int((datetime.datetime.now()
                             - datetime.datetime(2015,1,1))
                            .total_seconds()*100))
        else:
            jobid = None
        if source == 'pipeline':
            new_basename = hdr['PLDSID']
            logging.debug('Source=pipeline so using basename:{}'
                          .format(new_basename))
        else:
            new_basename = fn.generate_fname(*fname_fields,
                                             jobid=jobid,
                                             wunk=warn_unknown,
                                             orig=mirror_fname)


        ipath = pathlib.PurePath(mirror_fname
                                 .replace(mirror_dir, archive331))
        new_ipath = ipath.with_name(new_basename)
        new_ifname = str(new_ipath)
        new_ihdr = str(new_ipath.with_suffix('.hdr'))

        # Create hdr as temp file, i-put, delete tmp file (auto on close)
        # Archive requires extra fields prepended to hdr txt! :-<
        with tempfile.NamedTemporaryFile(mode='w', dir='/tmp') as f:
            ingesthdr = ('#filename = {filename}\n'
                         '#reference = {filename}\n'
                         '#filetype = UNKNOWN\n'
                         '#filesize = {filesize} bytes\n'
                         '#file_md5 = {checksum}\n\n'
                     )
            print(ingesthdr.format(filename=new_basename,
                                   filesize=os.path.getsize(mirror_fname),
                                   checksum='CHECKSUM'
                               ),
                  file=f)
            # Print without blank cards or trailing whitespace
            hdrstr = hdr.tostring(sep='\n',padding=False)
            print(*[s.rstrip() for s in hdrstr.splitlines()
                    if s.strip() != ''],
                  sep='\n',
                  file=f, flush=True)
            
            # The only reason we do this is to satisfy Archive Ingest!!!
            # Since it has to have a reference to the FITS file anyhow,
            # Archive Ingest SHOULD deal with the hdr.
            iu.irods_put331(f.name, new_ihdr)
            #! shutil.copy(f.name, '/home/vagrant/tmp/') #!!! REMOVE. diagnostic
            logging.debug('iput new_ihdr to: {}'.format(new_ihdr))

        # END with tempfile
        hdulist.flush()
        hdulist.close()
    except:
        traceback.print_exc()
        raise
    finally:
        pass
  
    iu.irods_put331(mirror_fname, new_ifname) # iput renamed FITS

    #
    # At this point both FITS and HDR are in archive331
    #

    logging.debug('prep_for_ingest: RETURN={}'.format(new_ihdr))
    return new_ihdr, new_ifname

##########
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
##########
#
def submit_to_archive(ifname, checksum, qname, qcfg=None):
    """Ingest a FITS file (really JUST Header) into the archive if
possible.  Ingest involves renaming to satisfy filename
standards. Although I've seen no requirements for it, previous systems
also used a specific 3 level directory structure that is NOT used
here. However the levels are stored in hdr fields SB_DIR{1,2,3}."""
    logging.debug('submit_to_archive({},{})'.format(ifname, qname))
    #! logging.debug('   qcfg={})'.format(qcfg))
    mirror_dir =  qcfg[qname]['mirror_dir']
    archive331 =  qcfg[qname]['archive_irods331']
    #!id_in_fname = qcfg[qname].get('id_in_fname',0)

    #!jidt = False if (id_in_fname == 0) else id_in_fname
    try:
        ihdr,destfname = prep_for_ingest(ifname, mirror_dir, archive331)
    except:
        #! traceback.print_exc()
        raise
    
    try:
        #!STUB_archive_ingest(new_fname, qname, qcfg=qcfg)
        http_archive_ingest(ihdr, checksum, qname, qcfg=qcfg)
    except:
        #! traceback.print_exc()
        raise

    return destfname


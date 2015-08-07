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
import subprocess
from copy import copy

from . import fits_utils as fu
from . import file_naming as fn
from . import exceptions as tex
from . import irods331 as iu
from . import ingest_decoder as idec
 

def http_archive_ingest(hdr_ipath, qname, qcfg=None, origfname='NA'):
    """Store ingestible FITS file and hdr in IRODS.  Pass location of hdr to
 Archive Ingest via REST-like interface."""
    import random # for stubbing random failures (not for production)

    logging.debug('EXECUTING: http_archive_ingest({}, {})'
                  .format(hdr_ipath, qname))

    # extract from qcfg ealier and pass dict (see prep_for_ingest)!!!
    arch_host = qcfg[qname]['arch_host']
    arch_port = qcfg[qname]['arch_port']
    irods_host = qcfg[qname]['arch_irods_host']
    irods_port = qcfg[qname]['arch_irods_port']
    prob_fail = qcfg[qname]['action_fail_probability']

    archserver_url = ('http://{}:{}/?hdrUri={}'
                     .format(arch_host, arch_port, hdr_ipath))
    logging.debug('archserver_url = {}'.format(archserver_url))

    result = True
    if qcfg[qname].get('disable_archive_svc',0) > 0:
        logging.warning('Ingest DISABLED. '
                        'http_archive_ingest() using prob_fail= {}'
                        .format(prob_fail))
        if random.random() <= prob_fail:
            raise tex.SubmitException(
                'Killed by cosmic ray with probability {}'
                .format(prob_fail))
    else:
        response = ''
        try:
            with urllib.request.urlopen(archserver_url) as f:
                # As of 1/15/2015 the only two possible responses are:
                #   "Success" or "Failure"
                #!response = f.readline().decode('utf-8')
                response = f.read().decode('utf-8')
            logging.debug('ARCH server response: {}'.format(response))
        except:
            raise
        success, operator_msg = idec.decodeIngest(response)
        logging.debug('ARCH server: success={}, msg={}'
                      .format(success, operator_msg))
        #!result = True if response == "Success" else False
        #!if not result:
        if not success:
            #! operator_msg = idec.decodeIngest(response)
            raise tex.SubmitException('HTTP response from NSA server for file {}: "{}"; {}'
            .format(origfname, response, operator_msg))

    return result
    

def prep_for_ingest(mirror_fname, **kwargs):
    """GIVEN: FITS absolute path
DO: 
  validate RAW fields
  Augment hdr. 
  validate AUGMENTED fields
  Add hdr as text file to irods331.
  Rename FITS to satisfy standards. 
  Add fits to irods331
  remove from mirror

mirror_fname :: Mountain mirror on valley
RETURN: irods location of hdr file.
    """

    #!logging.debug('prep_for_ingest: fname={}, m_dir={}, a_dir={}'
    #!              .format(mirror_fname, mirror_dir, archive331))

    # Name/values passed on LPR command line.
    #   e.g. lpr -P astro -o _INSTRUME=KOSMOS  -o _OBSERVAT=KPNO  foo.fits
    # Only use options starting with '_' and remove '_' from dict key.
    # +++ Add code here to handle other kinds of options passed from LPR.
    optfname = mirror_fname + ".options"
    optstr = ''
    if os.path.exists(optfname):
        with open(optfname,encoding='utf-8') as f:
            optstr = f.readline()
    options = dict()
    opt_params = dict()
    for opt in optstr.split():
        k, v = opt.split('=')
        if k[0] != '_':
            continue
        if k[1] == '_':
            opt_params[k[2:]] = v
        else:
            options[k[1:]] = v.replace('_', ' ')                
        
    # +++ API: under-under parameters via lp options
    jidt = opt_params.get('jobid_type',None)  # plain | seconds | (False)
    source = opt_params.get('source','raw')   # pipeline | (dome)
    warn_unknown = opt_params.get('warn_unknown', False) # 1 | (False)
    orig_fullname = opt_params.get('filename','<unknown>')

    #!logging.debug('Options in prep_for_ingest: {}'.format(options))
    #!logging.debug('Params  in prep_for_ingest: {}'.format(opt_params))

    hdr_ifname = "None"
    try:
        # augment hdr (add fields demanded of downstream process)
        hdulist = pyfits.open(mirror_fname, mode='update') # modify IN PLACE
        hdr = hdulist[0].header # use only first in list.
        fu.apply_options(options, hdr)
        hdr['DTNSANAM'] = 'NA' # we will set after we generate_fname, here to pass validate
        hdr['DTACQNAM'] = orig_fullname
        fu.validate_raw_hdr(hdr, orig_fullname)
        fname_fields = fu.modify_hdr(hdr, mirror_fname, options, opt_params,
                                     **kwargs)
        fu.validate_cooked_hdr(hdr, orig_fullname)
        fu.validate_recommended_hdr(hdr, orig_fullname)
        # Generate standards conforming filename
        # EXCEPT: add field when JIDT given.
        if jidt == 'plain':
            jobid = pathlib.PurePath(mirror_fname).parts[-2]
        elif jidt == 'seconds': 
            # hundredths of a second since 1/1/2015
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
        hdr['DTNSANAM'] = new_basename

        new_ipath = fn.generate_archive_path(hdr, source=source)
        ext = fu.fits_extension(new_basename)
        new_ipath = new_ipath / new_basename
        new_ifname = str(new_ipath)
        new_ihdr = new_ifname.replace(ext,'.hdr')
        logging.debug('new_ipath={}, new_basename={}, new_ifname={}'
                      .format(new_ipath, new_basename, new_ifname))

        # Print without blank cards or trailing whitespace
        hdrstr = hdr.tostring(sep='\n',padding=False)
        hdulist.flush()
        hdulist.close()         # now FITS header is MODIFIED
        md5 = subprocess.check_output("md5sum -b {} | cut -f1 -d' '"
                                      .format(mirror_fname),
                                      shell=True)
        md5sum=md5.decode().strip()
        filesize=os.path.getsize(mirror_fname)
        
        # Create hdr as temp file, i-put, delete tmp file (auto on close)
        # Archive requires extra fields prepended to hdr txt! :-<
        with tempfile.NamedTemporaryFile(mode='w', dir='/tmp') as f:
            ingesthdr = ('#filename = {filename}\n'
                         '#reference = {filename}\n'
                         '#filetype = TILED_FITS\n'
                         '#filesize = {filesize} bytes\n'
                         '#file_md5 = {checksum}\n\n'
                     )
            print(ingesthdr.format(filename=new_basename,
                                   filesize=filesize, checksum=md5sum),
                  file=f)
            print(*[s.rstrip() for s in hdrstr.splitlines()
                    if s.strip() != ''],
                  sep='\n',
                  file=f, flush=True)
            
            # The only reason we do this is to satisfy Archive Ingest!!!
            # Since it has to have a reference to the FITS file anyhow,
            # Archive Ingest SHOULD deal with the hdr.  Then again, maybe
            # ingest does NOT care about the FITS file at all!
            iu.irods_put331(f.name, new_ihdr)

        # END with tempfile
    except:
        traceback.print_exc()
        raise
        #! raise tex.SubmitException('Bad header content in file {}'
        #!                           .format(orig_fullname))
  
    #! iu.irods_put331(mirror_fname, new_ifname) # iput renamed FITS
    #
    # At this point both FITS and HDR are in archive331
    #

    logging.debug('prep_for_ingest: RETURN={}'.format(new_ihdr))
    return new_ihdr, new_ifname, orig_fullname
    # END prep_for_ingest()

##########
# (-sp-) GRIM DETAILS: The Archive Ingest process is ugly and the
# interface is not documented (AT ALL, as far as I can tell). It
# accepts a URI for an irods path of a "hdr" for a FITS file. The
# "hdr" has to be the hdr portion of a FITS with 5 lines prepended to
# it. Its more ugly because the submit (HTTP request) may fail but
# both the hdr and the fits irods file location cannot be changed if
# the submit succeeds.  But we want them to be a different place if
# the submit fails. So we have to move before the submit, then undo
# the move if it fails. The HTTP response may indicate failure, but I
# think it could indicate success even when there is a failure.  It
# would make perfect sense for the Archive Ingest to read what it
# needs directly from the FITS file (header). It can be done quickly
# even if the data portion of the FITS is large. Not doing so means
# extra complication and additional failure modes.  Worse, because a
# modified hdr has to be sent to Ingest, the actual fits file has to
# be accessed when otherwise we could have just dealt with irods
# paths. Fortunately, the irods icommand "iexecmd" lets us push such
# dirt to the server.
# 
# After a successful ingest, its possible that someone will try to
# ingest the same file again. Archive does not allow this so will fail
# on ingest.  Under such a circumstance the PREVIOUS hdr info would be
# in the database, but the NEW hdr (and FITS) would be in irods. Under
# such cirumstances, a user might retrieve a FITS file and find that
# is doesn't not match their query. To avoid such a inconsistency, we
# iput FITS only on success and restore the previous HDR on ingest
# failure.  Ingest will also fail with duplicate error if the file
# exists at a DIFFERENT irods path than the one we gave in hdrUri and
# it doesn't tell us what file it considered to be a duplicate!!!
# 
##########
#
def submit_to_archive(ifname, checksum, qname, qcfg=None):
    """Ingest a FITS file (really JUST Header) into the archive if
possible.  Ingest involves renaming to satisfy filename
standards. There are numerous under-the-hood requirements imposed by
how Archive works. See comments above for the grim details.

ifname:: full path of fits file (in mirror-archive)
checksum:: NOT USED
qname:: Name of queue from tada.conf (e.g. "transfer", "submit")

    """
    #!logging.debug('submit_to_archive({},{})'.format(ifname, qname))
    
    cfgprms = dict(mirror_dir =  qcfg[qname]['mirror_dir'],
                   archive331 =  qcfg[qname]['archive_irods331'],
                   mars_host  =  qcfg[qname].get('mars_host'),
                   mars_port  =  qcfg[qname].get('mars_port'),
                   )
    saved_hdr = None

    try:
        new_ihdr,destfname,origfname = prep_for_ingest(ifname, **cfgprms)
        saved_hdr = os.path.join('/var/tada', new_ihdr)
        foundHdr = iu.irods_get331(new_ihdr, saved_hdr)
    except:
        #! traceback.print_exc()
        raise
    
    try:
        http_archive_ingest(new_ihdr, qname, qcfg=qcfg, origfname=origfname)
    except:
        if foundHdr:
            iu.irods_put331(saved_hdr, new_ihdr) # restore saved hdr
        else:
            # hard to test this; may it hasn't been tested at all!
            iu.irods_remove331(new_ihdr) # remove our new hdr
        raise

    iu.irods_put331(ifname, destfname) # iput renamed FITS
    return destfname


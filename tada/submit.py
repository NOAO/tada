"Dirt needed to submit a fits file to the archive for ingest"

import sys
import argparse
import logging
import logging.config
import astropy.io.fits as pyfits
import os
import os.path
from pathlib import PurePath
import pathlib
import requests
import datetime
import shutil
import magic
import yaml
import hashlib
import socket
import warnings
from astropy.utils.exceptions import AstropyUserWarning

from . import fits_utils as fu
from . import file_naming as fn
from . import exceptions as tex
from . import irods331 as iu
from . import ingest_decoder as idec
from . import config
from . import audit
from . import utils as tut
from . import settings

warnings.simplefilter('ignore', category=AstropyUserWarning)

auditor = audit.Auditor()

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def http_archive_ingest(hdr_ipath, origfname='NA', ipfx='irods://'):
    """Store ingestible FITS file and hdr in IRODS.  Pass location of hdr to
Archive Ingest via REST-like interface. 
RETURN: (statusBool, message, operatorMessage)"""
    logging.debug('EXECUTING: http_archive_ingest({})'
                  .format(hdr_ipath))
    timeout = settings.arch_timeout
    archserver_url = ('http://{}:{}/'.format(settings.arch_host,
                                             settings.arch_port))
    payload = dict(hdrUri=ipfx+hdr_ipath)
    logging.debug('archserver_url={}, prms={}, timeout={}'
                  .format(archserver_url, payload, timeout))

    response = ''
    try:
        tut.tic()
        r = requests.get(archserver_url, params=payload, timeout=timeout)
        response = r.text
        logging.debug('archserver full url = {}'.format(r.url))
        elapsed = tut.toc()
        logging.debug('archserver response({:.2f}): {}'
                      .format(elapsed, response))
    except Exception as err:
        success = False
        ops_msg= ('Problem in opening or reading connection to: {}{}; {}'
                  .format(archserver_url, payload, err))
    else:
        success, ops_msg, mtype, itype = idec.decodeIngestResponse(response)
        logging.debug('ARCH server: success={}, msg={}, errcode={}'
                      .format(success, ops_msg, mtype))
        if itype == 'SUCCESS_WITH_WARNING':
            logging.warning('ARCH server: {}'.format(ops_msg))
    if not success:
        iu.irods_remove331(hdr_ipath)
        
    return (success, ops_msg)

    

def new_fits(orig_fitspath, changes, moddir=None):
    if moddir == None:
        # this had better be writable or we will fail to modify it
        # This file SHOULD be from cache so writable by us.
        modfilepath = orig_fitspath
    else:
        os.makedirs(moddir, exist_ok=True)
        modfilepath = shutil.copy(orig_fitspath, moddir)
        os.chmod(modfilepath, 0o664)

    logging.debug('new_fits({}, {}, moddir={})'
                  .format(orig_fitspath, changes, moddir))
    # Apply changes to header (MODIFY IN PLACE)
    hdulist = pyfits.open(modfilepath, mode='update') # modify IN PLACE
    fitshdr = hdulist[0].header # use only first in list.
    fitshdr.update(changes)
    #hdulist.flush()
    hdulist.close(output_verify='ignore')         # now FITS header is MODIFIED
    fu.scrub_fits(modfilepath)    
    fu.fitsverify(modfilepath)
    return modfilepath


def gen_hdr_file(fitsfilepath, new_basename):
    """Generate a text .hdr file.  Directory containing fitsfilepath must
    be writable.  That is where the hdr file will be written. Must
    write all HDUs because things like RA, DEC may get pushed to
    extension upon fpack.
    """
    hdrstr = ''
    # Print without blank cards or trailing whitespace.
    # Concatenate ALL HDUs into one string
    for hdu in pyfits.open(fitsfilepath):
        hdrstr += hdu.header.tostring(sep='\n', padding=False, endcard=False)
        hdrstr += '\n'
    hdrstr += 'END\n'

    # Archive cannot handle CONITNUE, turn multiple CARDS into one
    # (with length longer than standard allows)
    hdrstr = hdrstr.replace("&\'\nCONTINUE  \'","")
    
    md5sum = md5(fitsfilepath)
    
    filesize=os.path.getsize(fitsfilepath)

    # Archive requires extra fields prepended to hdr txt! :-<
    hdrfilepath = str(PurePath(fitsfilepath).parent
                      / fn.get_hdr_fname(new_basename))
    with open(hdrfilepath, mode='w') as f:
        ingesthdr = ('#filename = {filename}\n'
                     '#reference = {filename}\n'
                     '#filetype = TILED_FITS\n'
                     '#filesize = {filesize} bytes\n'
                     '#file_md5 = {checksum}\n\n'
                 )
        print(ingesthdr.format(filename=new_basename,
                               filesize=filesize,
                               checksum=md5sum),
              file=f)
        print(*[s.rstrip() for s in hdrstr.splitlines()
                if s.strip() != ''],
              sep='\n',
              file=f, flush=True)
    # END open
    return hdrfilepath
    
def prep_for_ingest(mirror_fname,
                    md5sum,
                    targetpath=None,
                    persona_options=None,  # e.g. (under "_DTSITE")
                    persona_params=None,   # e.g. (under,under) "__FOO"
                    moddir=None,
                    **kwargs):
    """GIVEN: FITS absolute path
DO: 
  validate RAW fields
  Augment hdr. 
  validate AUGMENTED fields
  Add hdr as text file to irods.
  Rename FITS to satisfy standards. 
  Add fits to irods
  remove from mirror

mirror_fname :: Mountain mirror on valley
RETURN: irods location of hdr file.
    """
    options = persona_options if  persona_options else dict()
    opt_params = persona_params if persona_params else dict()
    logging.debug('prep_for_ingest(): options={}, opt_params={}'
                  .format(options, opt_params))
    
    # +++ API: under-under parameters via lp options
    jidt = opt_params.get('jobid_type',None)  # plain | seconds | (False)
    tag = opt_params.get('job_tag','')
    source = opt_params.get('source','raw')   # pipeline | (dome)
    resubmit = int(opt_params.get('test_resubmit', '0')) # GT 0::try even if HDR exists, ==1::also log error

    orig_fullname = opt_params['filename']
    md5sum= opt_params['md5sum']
    #! hdr_ifname = "None"
    newhdr=dict()
    try:
        # augment newhdr (add fields demanded of downstream process)
        #! hdulist = pyfits.open(mirror_fname, mode='update') # modify IN PLACE
        #! newhdr = hdulist[0].header # use only first in list.
        newhdr = fu.get_hdr_as_dict(mirror_fname)
        if opt_params.get('OPS_PREAPPLY_UPDATE','no') == 'yes': #!!!
            fu.apply_options(options, newhdr)
        if 'DTACQNAM' not in newhdr:
            newhdr['DTACQNAM'] = orig_fullname
        # we will set DTNSANAM after we generate_fname, here to pass validate
        newhdr['DTNSANAM'] = 'NA' 
        fu.validate_raw_hdr(newhdr, orig_fullname)
        try:
            fu.fix_hdr(newhdr, mirror_fname, options, opt_params, **kwargs)
        except tex.IngestRejection:
            raise
        except tex.BadPropid as bpe:
            raise tex.IngestRejection(md5sum, orig_fullname, str(bpe), newhdr)
        except Exception as err:
            #!auditor.log_audit(md5sum, orig_fullname, False, '',  err, newhdr=newhdr)
            raise tex.IngestRejection(md5sum, orig_fullname, err, newhdr)
        fu.validate_cooked_hdr(newhdr, orig_fullname)
        if opt_params.get('VERBOSE', False):
            fu.validate_recommended_hdr(newhdr, orig_fullname)
        # Generate standards conforming filename
        # EXCEPT: add field when JOBID_TYPE and/or JOB_TAG given.
        jtypes=set(['plain', 'obsmicro', 'seconds'])
        if jidt != None and jidt not in jtypes:
            logging.warning(('Got unexpected value {} for "jobid_type"'
                             ' in personality file. (allowed={})'
                             .format(jidt, jtypes)))
        if jidt == 'plain':
            jobid = pathlib.PurePath(mirror_fname).parts[-2]
            tag = jobid
        elif jidt == 'obsmicro':
            # use microseconds from DATE-OBS
            logging.debug('Using microseconds from DATE-OBS: {} of {}'
                          .format(newhdr['DATE-OBS'], mirror_fname))
            parts = newhdr['DATE-OBS'].split('.')
            jobid = '0' if len(parts) < 2 else parts[1]
            tag = jobid if tag == '' else (jobid + '_' + tag)
        elif jidt == 'seconds': 
            # hundredths of a second since 1/1/2015
            jobid = str(int((datetime.datetime.now()
                             - datetime.datetime(2015,1,1)) 
                            .total_seconds()*100))
            tag = jobid if tag == '' else (jobid + '_' + tag)

        #ext = fn.fits_extension(orig_fullname)
        ext = fn.fits_extension(mirror_fname)
        if source == 'pipeline':
            new_basename = os.path.basename(orig_fullname)
            logging.debug('Source=pipeline so using basename:{}'
                          .format(new_basename))
        elif targetpath != None:
            new_basename = os.path.basename(targetpath)
        else:
            new_basename = fn.generate_fname(newhdr, ext,
                                             tag=tag,
                                             orig=mirror_fname)
        newhdr['DTNSANAM'] = new_basename
        new_ipath = (fn.generate_archive_path(newhdr, source=source)/new_basename
                     if targetpath == None
                     else PurePath('/noao-tuc-z1/hlsp',
                                   targetpath))
        logging.debug('orig_fullname={}, new_basename={}, ext={}'
                      .format(orig_fullname, new_basename, ext))
        new_ifname = str(new_ipath)
        new_ihdr = new_ifname.replace(ext,'hdr')
        logging.debug('new_ifname={},new_ihdr={}'.format(new_ifname, new_ihdr))

        if opt_params.get('dry_run','no') == 'yes':
            logging.debug('Doing dry_run (no ingest)')
            msg= ('SUCCESS: DRY-RUN of ingest {} as {}'
                  .format(mirror_fname, new_ifname))
            raise tex.SuccessfulNonIngest(msg)

        # Abort ingest if either HDR or FITS already exist under irods
        if iu.irods_exists331(new_ihdr):
            msg = ('iRODS HDR file already exists at {} on submit of {}.'
                   .format(new_ihdr, orig_fullname))
            if resubmit == 1:
                logging.error(msg + ' Trying to ingest anyhow.')
            elif resubmit > 1:
                pass
            else:
                msg = msg + ' Aborting attempt to ingest.'
                logging.error(msg)
                raise tex.IrodsContentException(msg)
        elif iu.irods_exists331(new_ifname):
            msg = ('iRODS FITS file already exists at {} on submit of {}.'
                   .format(new_ifname, orig_fullname))
            if resubmit == 1:
                logging.error(msg + ' Trying to ingest anyhow.')
            elif resubmit > 1:
                pass
            else:
                msg = msg + ' Aborting attempt to ingest.'
                logging.error(msg)
                raise tex.IrodsContentException(msg)

        # Create final (modified) FITS
        newfits = new_fits(mirror_fname, newhdr, moddir=moddir)

        hdrfile = gen_hdr_file(newfits, new_basename)
        iu.irods_put331(hdrfile, new_ihdr)
        os.remove(hdrfile)        
    except tex.IngestRejection:
        raise
    except tex.InvalidFits as ife:
        raise tex.IngestRejection(md5sum, orig_fullname, str(ife), newhdr) 
    except Exception as err:
        raise tex.IngestRejection(md5sum, orig_fullname, err, newhdr)

    #
    # At this point both FITS and HDR are in archive331
    #

    logging.debug('prep_for_ingest: RETURN={}'.format(new_ihdr))
    return new_ihdr, new_ifname, newhdr, newfits
    # END prep_for_ingest()


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

def unprotected_submit(ifname, dome_md5):
    """Called from ACTION queue.
Try to modify headers and submit FITS to archive. If anything fails 
more than N times, move the queue entry to Inactive. (where N is the 
configuration field: maximum_errors_per_record)
    ifname:: absolute path (cache)
"""
    logging.debug('EXECUTING unprotected_submit: {}, {}'.format(ifname, dome_md5))
    noarc_root =  '/var/tada/anticache'
    mirror_root = '/var/tada/cache'    
    auditor.set_fstop(dome_md5, 'valley:cache', host=socket.getfqdn())

    try:
        ftype = file_type(ifname)
    except tex.IngestRejection:
        raise
    except Exception as ex:
        logging.error('Execution failed: {}; ifname={}'.format(ex, ifname))
        raise tex.IngestRejection(dome_md5, ifname, ex, dict())
        
    destfname = None
    if 'FITS' == ftype :  # is FITS
        msg = 'FITS_file'
        popts, pprms = fu.get_options_dict(ifname) # .yaml 
        origfname = pprms['filename']
        destfname,newhdr = submit_to_archive(ifname, dome_md5)
        logging.debug('SUCCESSFUL submit; {} as {}'.format(ifname, destfname))
        os.remove(ifname)
        optfname = ifname + ".options"
        logging.debug('Remove possible options file: {}'.format(optfname))
        if os.path.exists(optfname):
            os.remove(optfname)

    else: # not FITS
        destfname = ifname.replace(mirror_root, noarc_root)
        os.makedirs(os.path.dirname(destfname), exist_ok=True)
        shutil.move(ifname, destfname)
        auditor.set_fstop(dome_md5, 'valley:anticache', host=socket.getfqdn())
        msg = 'Non-FITS file: {}'.format(ifname)
        #! logging.warning('Failed to mv non-fits file from mirror on Valley.')
        auditor.set_fstop(dome_md5, 'mountain:anticache', host=socket.getfqdn())
        # Remove files if noarc_root is taking up too much space (FIFO)!!!
        raise tex.IngestRejection(dome_md5, ifname, msg, dict())
        
    auditor.set_fstop(dome_md5,'archive')
    #!auditor.log_audit(dome_md5, origfname, True, destfname, '', newhdr=newhdr)
    return True
# END unprotected_submit action


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
def submit_to_archive(ifname, checksum, moddir=None):
    """Ingest a FITS file (really JUST Header) into the archive if
possible.  Ingest involves renaming to satisfy filename
standards. There are numerous under-the-hood requirements imposed by
how Archive works. See comments above for the grim details.

ifname:: full path of fits file (in cache)
checksum:: checksum of original file

    """
    logging.debug('submit_to_archive({})'.format(ifname))
    
    #!popts, pprms = fu.get_options_dict(ifname + ".options")
    orighdr = fu.get_hdr_as_dict(ifname)
    popts, pprms = fu.get_options_dict(ifname) # .yaml 
    logging.debug('submit_to_archive(popts={},pprms={})'.format(popts, pprms))
    origfname = pprms['filename']
    md5sum = checksum
    if 'do_audit' in pprms:
        auditor.do_svc = pprms['do_audit']

    try:
        # Following does irods_put331 to new_ihdr if the hdr looks valid
        new_ihdr,destfname,changed,modfits = prep_for_ingest(
            ifname,
            md5sum,
            persona_options=popts,
            persona_params=pprms,
            moddir=None)
    except: # Exception as err:
        raise
    (success, ops_msg) = http_archive_ingest(new_ihdr, origfname=origfname)
        
    if moddir != None:
        os.remove(modfits)

    auditor.log_audit(md5sum, origfname, success, destfname, ops_msg, orighdr=orighdr, newhdr=changed)
    if not success:
        raise tex.IngestRejection(md5sum, origfname, ops_msg, orighdr)

    iu.irods_put331(modfits, destfname) # iput renamed FITS
    logging.info('SUCCESSFUL submit_to_archive; {} as {}'
                 .format(origfname, destfname))
    return destfname, changed


#!def protected_direct_submit(fitsfile, moddir,
#!                  personality=None, # dictionary from YAML 
#!                  trace=False):
#!    """Blocking submit to archive without Queue. 
#!Waits for ingest service to complete and returns its formated result.
#!Traps for reasonable errors and returns those in returned value. 
#!So, caller should not have to put this function in try/except."""
#!    logging.debug('EXECUTING: protected_direct_submit({}, personality={},'
#!                  'moddir={})'
#!                  .format(fitsfile, personality,  moddir))
#!    md5sum = md5(fitsfile)
#!    ok = True  
#!    statusmsg = None
#!    if 'FITS image data' not in str(magic.from_file(fitsfile)):
#!        errmsg = 'Cannot ingest non-FITS file: {}'.format(fitsfile)
#!        logging.error(errmsg)
#!        auditor.log_audit(md5sum, fitsfile, False, '', errmsg)
#!        return (False, errmsg)
#!
#!
#!    if personality == None:
#!        personality = dict(params={}, options={})
#!    if 'filename' not in personality['params']:
#!        personality['params']['filename'] = fitsfile
#!
#!    pprms = personality['params']
#!    popts = personality['options']
#!    md5sum = pprms['md5sum']
#!    logging.debug('direct_submit: popts={}'.format(popts))
#!    logging.debug('direct_submit: pprms={}'.format(pprms))
#!    origfname = fitsfile
#!    try:
#!        new_ihdr, destfname, changed, modfits = prep_for_ingest(fitsfile,
#!                                                                md5sum,
#!                                                       persona_options=popts,
#!                                                       persona_params=pprms,
#!                                                       moddir=moddir)
#!    except Exception as err:
#!        tut.trace_if(trace)
#!        msg = str(err)
#!        logging.error(msg)
#!        auditor.log_audit(md5sum, origfname, False, '', str(err), newhdr=popts)
#!        return (False, msg)
#!
#!    success, ops_msg = http_archive_ingest(new_ihdr, origfname=origfname)
#!    auditor.log_audit(md5sum, origfname, success, destfname, ops_msg, orighdr=popts, newhdr=changed)
#!    if not success:
#!        if moddir != None:
#!            os.remove(modfits)
#!            logging.debug('DBG: Removed modfits={}; moddir={}'
#!                          .format(modfits, moddir))
#!        return(False, 'FAILED: {} not archived; {}'.format(fitsfile, ops_msg))
#!    else:
#!        # iput renamed, modified FITS
#!        iu.irods_put331(modfits, destfname) # iput renamed FITS
#!        if moddir != None:
#!            os.remove(modfits)
#!            logging.debug('DBG: Removed modfits={}; moddir={}'
#!                          .format(modfits, moddir))
#!        return(True, 'SUCCESS: archived {} as {}'.format(fitsfile, destfname))
#!    return (ok, statusmsg)
#!    # END: protected_direct_submit()
    
##############################################################################
def direct_submit(fitsfile, moddir,
                  personality_files=[],
                  personality=None, # dictionary from YAML
                  target=None,
                  trace=False):
    logging.debug('EXECUTING: direct_submit({}, '
                  'personality={}, personality_files={}, '
                  'moddir={}, target={})'
                  .format(fitsfile, personality, personality_files,
                          moddir, target))
    warnings.simplefilter('ignore', category=AstropyUserWarning)
    md5sum = md5(fitsfile)

    if 'FITS image data' not in str(magic.from_file(fitsfile)):
        errmsg = 'Cannot ingest non-FITS file: {}'.format(fitsfile)
        logging.error(errmsg)
        auditor.log_audit(md5sum, fitsfile, False, '', errmsg)
        auditor.set_fstop(md5sum, 'valley:direct', host=socket.getfqdn())
        sys.exit(errmsg)
        
    success = True
    statuscode = 0    # for sys.exit(statuscode)
    statusmsg = 'NA'

    orighdr = fu.get_hdr_as_dict(fitsfile)
    popts = dict()
    pprms = dict()
    for pf in personality_files:
        po, pp = fu.get_personality_dict(pf)        
        popts.update(po)
        pprms.update(pp)
    if 'filename' not in pprms:
        pprms['filename'] = fitsfile
    if personality:
        pprms.update(personality['params'])
        popts.update(personality['options'])
    logging.debug('direct_submit: popts={}'.format(popts))
    logging.debug('direct_submit: pprms={}'.format(pprms))
    origfname = fitsfile
    changed = dict()
    try:
        new_ihdr,destfname,changed,modfits = prep_for_ingest(
            fitsfile,
            md5sum,
            targetpath=target,
            persona_options=popts,
            persona_params=pprms,
            moddir=moddir)
    except Exception as err:
        tut.trace_if(trace)
        statusmsg = str(err)
        #statusmsg = err.errmsg
        success = False
        statuscode = 1
        auditor.log_audit(md5sum, origfname, False, '', str(err), orighdr=orighdr, newhdr=changed)
        auditor.set_fstop(md5sum, 'valley:direct', host=socket.getfqdn())
        sys.exit(statusmsg)

        
    success, ops_msg = http_archive_ingest(new_ihdr, origfname=origfname)
    auditor.log_audit(md5sum, origfname, success, destfname, ops_msg, orighdr=orighdr, newhdr=changed)
    auditor.set_fstop(md5sum, 'valley:direct', host=socket.getfqdn())
    if not success:
        statusmsg = 'FAILED: {} not archived; {}'.format(fitsfile, ops_msg)
        statuscode = 2
    else:
        # iput renamed, modified FITS
        iu.irods_put331(modfits, destfname) # iput renamed FITS

        statusmsg= 'SUCCESS: archived {} as {}'.format(fitsfile, destfname)
        statuscode = 0

    print(statusmsg, file=sys.stderr)
    if moddir != None:
        os.remove(modfits)
        logging.debug('DBG: Removed modfits={}; moddir={}'
                      .format(modfits, moddir))
    sys.exit(statuscode)
 
def main():
    'Direct access to TADA submit-to-archive, without using queue.'
    #print('EXECUTING: {}\n\n'.format(' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Submit file to Noao Science Archive',
        epilog='EXAMPLE: %(prog)s myfile.fits'
    )
    parser.add_argument('fitsfile',
                        help='FITS file to ingest into archive',
                        type=argparse.FileType('rb')
    )
    parser.add_argument('-p', '--personality',
                        action='append',
                        default=[],
                        help='Personality file used to modify FITS header. Multiple allowed.',
                        type=argparse.FileType('rt')
    )

    dflt_moddir = os.path.expanduser('~/.tada/submitted')
    dflt_config = '/etc/tada/tada.conf'
    logconf='/etc/tada/pop.yaml'
    parser.add_argument('-m', '--moddir',
                        default=dflt_moddir,
                        help="Directory that will contain the (possibly modified, possibly renamed) file as submitted. Deleted after iRODS put. [default={}]".format(dflt_moddir),
                        )
    parser.add_argument('--logconf',
                        help='Logging configuration file (YAML format).'
                        '[Default={}]'.format(logconf),
                        default=logconf,
                        type=argparse.FileType('r'))
    parser.add_argument('-c', '--config',
                        default=dflt_config,
                        help='Config file. [default={}]'.format(dflt_config),
                        )
    parser.add_argument('--target',
                        help='Relative irods path to store FITS into')
    parser.add_argument('--trace',
                        action='store_true',
                        help='Produce stack trace on error')

    parser.add_argument('--loglevel', '-l', 
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.fitsfile.close()
    args.fitsfile = args.fitsfile.name
    pers_list = [p.name for p in args.personality]


    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel) 
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')

    logDict = yaml.load(args.logconf)
    logging.config.dictConfig(logDict)
    logging.getLogger().setLevel(log_level)
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])


    ############################################################################

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    #!qcfg, dirs = config.get_config(None,
    #!                               validate=False,
    #!                               yaml_filename=args.config)

    if args.target and args.target[0] == '/':
        args.target = args.target[1:] # insure it is relative
    direct_submit(args.fitsfile, args.moddir,
                  personality_files=pers_list,
                  target=args.target,
                  trace=args.trace)
    
if __name__ == '__main__':
    main()


"Dirt needed to submit a fits file to the archive for ingest"

import sys
import argparse
import logging
import logging.config
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
import shutil
import magic
import yaml
from copy import copy
import json

from . import fits_utils as fu
from . import file_naming as fn
from . import exceptions as tex
from . import irods331 as iu
from . import ingest_decoder as idec
from . import config

def audit_svc(source_pathname, archive_filename, status, metadatadict,
              ws_host='mars.sdm.noao.edu', ws_port=8000, svc_timeout=1):
    """Add audit record to svc."""
    if ws_host == None or ws_port == None:
        logging.error('Missing AUDIT host ({}) or port ({}).'
                      .format(host,port))
        return False
    logging.debug('Adding audit record')
    url = 'http://{}:{}/audit/add'.format(ws_host, ws_port)
    ddict = dict(source = source_pathname,
                 archive = archive_filename,
                 status = status,
                 metadata = metadatadict,  #updated metadata fields
                 )
    data = bytes(json.dumps(ddict), 'utf-8')
    req = urllib.request.Request(url)
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, data=data, timeout=svc_timeout) as f:
            response = f.read().decode('utf-8')
            #!logging.debug('MARS: server response="{}"'.format(response))
            return response
    except  Exception as err:
        logging.error('AUDIT: Error contacting service via "{}"; {}'
                      .format(url, str(err)))
        return False
    return True


def http_archive_ingest(hdr_ipath, qname, qcfg=None, origfname='NA'):
    """Store ingestible FITS file and hdr in IRODS.  Pass location of hdr to
Archive Ingest via REST-like interface. 
RETURN: (statusBool, message, operatorMessage)"""
    #!import random # for stubbing random failures (not for production)

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

    #!if qcfg[qname].get('disable_archive_svc',0) > 0:
    #!    logging.warning('Ingest DISABLED. '
    #!                    'http_archive_ingest() using prob_fail= {}'
    #!                    .format(prob_fail))
    #!    if random.random() <= prob_fail:
    #!        raise tex.SubmitException(
    #!            'Killed by cosmic ray with probability {}'
    #!            .format(prob_fail))
    #!else:
    response = ''
    try:
        with urllib.request.urlopen(archserver_url) as f:
            response = f.read().decode('utf-8')
        logging.debug('ARCH server response: {}'.format(response))
    except:
        raise
    success, operator_msg = idec.decodeIngest(response)
    logging.debug('ARCH server: success={}, msg={}'
                  .format(success, operator_msg))
    message = operator_msg
    if not success:
        #! operator_msg = idec.decodeIngest(response)
        message = ('HTTP response from NSA server for file {}: "{}"; {}'
                   .format(origfname, response, operator_msg))
        #raise tex.SubmitException(message)

    return (success, message, operator_msg)


def iput_modified_fits(ifname, destfname, changed,
                       moddir=None):
    """IPUT modified version of IFNAME to DESTFNAME after updating its
header to reflect content of CHANGED dict. If MODDIR given, use it for tempoerary modified file but delete after iput."""
    if moddir != None:
        os.makedirs(moddir, exist_ok=True)
        modfile = shutil.copy(ifname, moddir)
        os.chmod(modfile, 0o664)
    else:
        # this had better be writable or we will fail to modify it
        # This file SHOULD be from mountain-mirror so writable by us.
        modfile = ifname
        
    hdulist = pyfits.open(modfile, mode='update') # modify IN PLACE
    fitshdr = hdulist[0].header # use only first in list.
    fitshdr.update(changed)
    hdulist.flush()
    hdulist.close()         # now FITS header is MODIFIED
    iu.irods_put331(modfile, destfname) # iput renamed FITS
    if moddir != None:
        os.remove(modfile)
        logging.debug('DBG: Removed modfile={}'.format(modfile))

def prep_for_ingest(mirror_fname,
                    persona_options=dict(),  # e.g. (under "__DTSITE"
                    persona_params=dict(),   # e.g. (under,under) "__FOO"
                    moddir=None,
                    **kwargs):
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
    options = persona_options
    opt_params = persona_params
    #!logging.debug('prep_for_ingest(): options={}, opt_params={}'
    #!              .format(options, opt_params))
    
    # +++ API: under-under parameters via lp options
    jidt = opt_params.get('jobid_type',None)  # plain | seconds | (False)
    tag = opt_params.get('job_tag','')
    source = opt_params.get('source','raw')   # pipeline | (dome)
    resubmit = opt_params.get('test_resubmit', '0') == '1'
    
    # We want "filename" to always be given an option.
    # But we also don't want to force setting of options if we can
    # avoid it. So we use the only fname available: mirror_fname.
    orig_fullname = opt_params.get('filename',mirror_fname)

    hdr_ifname = "None"
    try:
        # augment hdr (add fields demanded of downstream process)
        #! hdulist = pyfits.open(mirror_fname, mode='update') # modify IN PLACE
        #! hdr = hdulist[0].header # use only first in list.
        hdr = fu.get_hdr_as_dict(mirror_fname)
        if opt_params.get('OPS_PREAPPLY_UPDATE','NO') == 'YES': #!!!
            fu.apply_options(options, hdr)
        hdr['DTACQNAM'] = orig_fullname
        # we will set DTNSANAM after we generate_fname, here to pass validate
        hdr['DTNSANAM'] = 'NA' 
        fu.validate_raw_hdr(hdr, orig_fullname)
        try:
            fname_fields = fu.fix_hdr(hdr, mirror_fname,
                                      options, opt_params, **kwargs)
        except Exception as err:
            raise tex.CannotModifyHeader('Could not update FITS header; '
                                         '{}'.format(err))
        fu.validate_cooked_hdr(hdr, orig_fullname)
        fu.validate_recommended_hdr(hdr, orig_fullname)
        # Generate standards conforming filename
        # EXCEPT: add field when JOBID_TYPE and/or JOB_TAG given.
        if jidt == 'plain':
            jobid = pathlib.PurePath(mirror_fname).parts[-2]
            tag = jobid
        elif jidt == 'seconds': 
            # hundredths of a second since 1/1/2015
            jobid = str(int((datetime.datetime.now()
                             - datetime.datetime(2015,1,1)) 
                            .total_seconds()*100))
            tag = jobid if tag == '' else (jobid + '_' + tag)

        ext = fn.fits_extension(orig_fullname)
        if source == 'pipeline':
            new_basename = hdr['PLDSID'] + ".fits.fz"
            logging.debug('Source=pipeline so using basename:{}'
                          .format(new_basename))
        else:
            new_basename = fn.generate_fname(hdr, ext,
                                             #! jobid=jobid,
                                             tag=tag,
                                             orig=mirror_fname)
        hdr['DTNSANAM'] = new_basename
        new_ipath = fn.generate_archive_path(hdr, source=source) / new_basename
        ext = fn.fits_extension(new_basename)
        logging.debug('orig_fullname={}, new_basename={}, ext={}'
                      .format(orig_fullname, new_basename, ext))
        new_ifname = str(new_ipath)
        new_ihdr = new_ifname.replace(ext,'hdr')
        logging.debug('new_ifname={},new_ihdr={}'.format(new_ifname, new_ihdr))

        if opt_params.get('dry_run','0') == '1':
            logging.debug('Doing dry_run (no ingest)')
            msg= ('SUCCESS: DRY-RUN of ingest {} as {}'
                  .format(mirror_fname, new_ifname))
            raise tex.SuccessfulNonIngest(msg)

        # Abort ingest if either HDR or FITS already exist under irods
        if iu.irods_exists331(new_ihdr):
            msg = ('iRODS HDR file already exists at {} on submit of {}.'
                   .format(new_ihdr, orig_fullname))
            if resubmit:
                logging.error(msg + ' Trying to ingest anyhow.')
            else:
                msg = msg + ' Aborting attempt to ingest.'
                logging.error(msg)
                raise tex.IrodsContentException(msg)
        elif iu.irods_exists331(new_ifname):
            msg = ('iRODS FITS file already exists at {} on submit of {}.'
                   .format(new_ifname, orig_fullname))
            if resubmit:
                logging.error(msg + ' Trying to ingest anyhow.')
            else:
                msg = msg + ' Aborting attempt to ingest.'
                logging.error(msg)
                raise tex.IrodsContentException(msg)

        
        # Print without blank cards or trailing whitespace
        fitshdr = pyfits.getheader(mirror_fname)
        fitshdr.update(hdr)
        hdrstr = fitshdr.tostring(sep='\n',padding=False)
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
        #!traceback.print_exc()
        raise
        #! raise tex.SubmitException('Bad header content in file {}'
        #!                           .format(orig_fullname))


        
    #! iu.irods_put331(mirror_fname, new_ifname) # iput renamed FITS
    #
    # At this point both FITS and HDR are in archive331
    #

    logging.debug('prep_for_ingest: RETURN={}'.format(new_ihdr))
    return new_ihdr, new_ifname, hdr
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
    
    cfgprms = dict(#mirror_dir =  qcfg[qname]['mirror_dir'],
                   archive331 =  qcfg[qname]['archive_irods331'],
                   mars_host  =  qcfg[qname].get('mars_host'),
                   mars_port  =  qcfg[qname].get('mars_port'),
                   )
    saved_hdr = None

    #!popts, pprms = fu.get_options_dict(ifname + ".options")
    popts, pprms = fu.get_options_dict(ifname) # .yaml or .options
    logging.debug('submit_to_archive(popts={},pprms={})'.format(popts, pprms))
    origfname = pprms.get('filename',ifname)
    try:
        # Following does irods_put331 to new_ihdr if the hdr looks valid
        new_ihdr,destfname,changed = prep_for_ingest(ifname,
                                                     persona_options=popts,
                                                     persona_params=pprms,
                                                     **cfgprms)
    except:
        #! traceback.print_exc()
        raise
    
    (success, msg, ops_msg) = http_archive_ingest(new_ihdr, qname,
                                                 qcfg=qcfg, origfname=origfname)
    if pprms.get('do_audit',False):
        audit_svc(origfname, destfname, ops_msg, popts)
    if not success:
        raise tex.SubmitException(msg)

    #!iu.irods_put331(ifname, destfname) # iput renamed FITS
    iput_modified_fits(ifname, destfname, changed) # iput renamed FITS
    return destfname


def protected_direct_submit(fitsfile, moddir,
                  personality=None, # dictionary from YAML 
                  qname='submit',
                  qcfg=None,
                  trace=False):
    """Blocking submit to archive without Queue. 
Waits for ingest service to complete and returns its formated result.
Traps for reasonable errors and returns those in returned value. 
So, caller should not have to put this function in try/except."""
    logging.debug('EXECUTING: protected_direct_submit({}, personality={},'
                  'moddir={})'
                  .format(fitsfile, personality,  moddir))
    ok = True  
    statusmsg = None
    if 'FITS image data' not in str(magic.from_file(fitsfile)):
        msg = 'Cannot ingest non-FITS file: {}'.format(fitsfile)
        logging.error(msg)
        return (False, msg)

    cfgprms = dict(mirror_dir =  qcfg[qname].get('mirror_dir'),
                   archive331 =  qcfg[qname].get('archive_irods331'),
                   mars_host  =  qcfg[qname].get('mars_host'),
                   mars_port  =  qcfg[qname].get('mars_port'),
                   )

    if personality == None:
        personality = dict(params={}, options={})
    if 'filename' not in personality['params']:
        personality['params']['filename'] = fitsfile

    pprms = personality['params']
    popts = personality['options']
    logging.debug('direct_submit: popts={}'.format(popts))
    logging.debug('direct_submit: pprms={}'.format(pprms))
    origfname = fitsfile
    try:
        new_ihdr, destfname, changed = prep_for_ingest(fitsfile,
                                                       persona_options=popts,
                                                       persona_params=pprms,
                                                       **cfgprms)
    except Exception as err:
        if trace:
            traceback.print_exc()
        msg = str(err)
        logging.error(msg)
        return (False, msg)

    success, m1, ops_msg = http_archive_ingest(new_ihdr, qname,
                                               qcfg=qcfg, origfname=origfname)
    if pprms.get('do_audit', '0') == '1':
        audit_svc(origfname, destfname, ops_msg, popts)
    if not success:
        return(False, 'FAILED: {} not archived; {}'.format(fitsfile, ops_msg))
    else:
        # iput renamed, modified FITS
        iput_modified_fits(fitsfile, destfname, changed, moddir=moddir)
        return(True, 'SUCCESS: archived {} as {}'.format(fitsfile, destfname))

    return (ok, statusmsg)
    # END: protected_direct_submit()
    
##############################################################################
def direct_submit(fitsfile, moddir,
                  personality_files=[],
                  personality=None, # dictionary from YAML 
                  qname='submit',
                  qcfg=None,
                  trace=False):
    logging.debug('EXECUTING: direct_submit({}, personality={}, personality_files={}, '
                  'moddir={})'
                  .format(fitsfile, personality, personality_files, moddir))
    if 'FITS image data' not in str(magic.from_file(fitsfile)):
        logging.error('Cannot ingest non-FITS file: {}'.format(fitsfile))
        sys.exit('Cannot ingest non-FITS file: {}'.format(fitsfile))
        
    success = True
    statuscode = 0    # for sys.exit(statuscode)
    statusmsg = 'NA'
    cfgprms = dict(#mirror_dir =  qcfg[qname]['mirror_dir'],
                   archive331 =  qcfg[qname]['archive_irods331'],
                   mars_host  =  qcfg[qname].get('mars_host'),
                   mars_port  =  qcfg[qname].get('mars_port'),
                   )
    saved_hdr = None

    popts = dict()
    pprms = dict()
    for pf in personality_files:
        po, pp = fu.get_personality_dict(pf)        
        popts.update(po)
        pprms.update(pp)
    pprms['filename'] = fitsfile
    if personality:
        pprms.update(personality['params'])
        popts.update(personality['options'])
    logging.debug('direct_submit(params={},options={})'.format(pprms, popts))

    logging.debug('direct_submit: popts={}'.format(popts))
    logging.debug('direct_submit: pprms={}'.format(pprms))
    origfname = fitsfile
    try:
        new_ihdr,destfname,changed = prep_for_ingest(fitsfile,
                                                     persona_options=popts,
                                                     persona_params=pprms,
                                                     **cfgprms)
    except Exception as err:
        if trace:
            traceback.print_exc()
        statusmsg = str(err)
        success = False
        statuscode = 1
        sys.exit(statusmsg)

        
    success,m1,ops_msg = http_archive_ingest(new_ihdr, qname,
                                         qcfg=qcfg, origfname=origfname)
    if pprms.get('do_audit','0') == '1':
        audit_svc(origfname, destfname, ops_msg, popts)
    if not success:
        statusmsg = 'FAILED: {} not archived; {}'.format(fitsfile, ops_msg)
        statuscode = 2
    else:
        #!iu.irods_put331(newfile, destfname) # iput renamed FITS
        # iput renamed, modified FITS
        iput_modified_fits(fitsfile, destfname, changed, moddir=moddir) 
        statusmsg= 'SUCCESS: archived {} as {}'.format(fitsfile, destfname)
        statuscode = 0

    print(statusmsg, file=sys.stderr)
    sys.exit(statuscode)
 
def main():
    'Direct access to TADA submit-to-archive, without using queue.'
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
    #!parser.add_argument('-t', '--timeout',
    #!                    type=int,
    #!                    help='Seconds to wait for Archive to respond',
    #!                    )
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
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    logDict = yaml.load(args.logconf)
    logging.config.dictConfig(logDict)
    logging.getLogger().setLevel(log_level)


    ############################################################################

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    qname = 'submit'
    qcfg, dirs = config.get_config(None,
                                   validate=False,
                                   json_filename=args.config)

    # out=`sudo -u tada sh -c "direct_submit --loglevel=DEBUG /data/bok/20150706/d7210.0008.fits.fz -p /sandbox/tada-cli/personalities/bok.personality 2>&1"`
    # out=`fits_submit -p bok /data/bok/20150706/d7210.0008.fits.fz `
    direct_submit(args.fitsfile, args.moddir,
                  personality_files=pers_list,
                  trace=args.trace,
                  qcfg=qcfg
                  )
    
if __name__ == '__main__':
    main()


"Dirt needed to submit a fits file to the archive for ingest"

import sys
import argparse
import logging
import logging.config
import astropy.io.fits as pyfits
import os
import os.path
from pathlib import PurePath
import traceback
import pathlib
import urllib.request
import datetime
#import subprocess
import shutil
import magic
import yaml
import hashlib



from . import fits_utils as fu
from . import file_naming as fn
from . import exceptions as tex
from . import irods331 as iu
from . import ingest_decoder as idec
from . import config
from . import audit


qcfg, dirs = config.get_config(None,
                               validate=False,
                               yaml_filename='/etc/tada/tada.conf')
auditor = audit.Auditor(qcfg.get('mars_host'),
                        qcfg.get('mars_port'),
                        qcfg.get('do_audit',True))


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def http_archive_ingest(hdr_ipath, qname, qcfg=None, origfname='NA'):
    """Store ingestible FITS file and hdr in IRODS.  Pass location of hdr to
Archive Ingest via REST-like interface. 
RETURN: (statusBool, message, operatorMessage)"""
    logging.debug('EXECUTING: http_archive_ingest({}, {})'
                  .format(hdr_ipath, qname))

    # extract from qcfg ealier and pass dict (see prep_for_ingest)!!!
    arch_host = qcfg['arch_host']
    arch_port = qcfg['arch_port']

    archserver_url = ('http://{}:{}/?hdrUri={}'
                     .format(arch_host, arch_port, hdr_ipath))
    logging.debug('archserver_url = {}'.format(archserver_url))

    response = ''
    try:
        with urllib.request.urlopen(archserver_url) as f:
            response = f.read().decode('utf-8')
        logging.debug('ARCH server response: {}'.format(response))
    except:
        raise tex.ArchiveWebserviceProblem(
            'Problem in opening or reading connection to: '
            .format(archserver_url))

    success, operator_msg, itype = idec.decodeIngest(response)
    logging.debug('ARCH server: success={}, msg={}'
                  .format(success, operator_msg))
    message = operator_msg
    if not success:
        message = ('HTTP response from NSA server for file {}: "{}"; {}'
                   .format(origfname, response, operator_msg))
        #raise tex.SubmitException(message)

    return (success, message, operator_msg, itype)


def new_fits(orig_fitspath, changes, moddir=None):
    if moddir == None:
        # this had better be writable or we will fail to modify it
        # This file SHOULD be from cache so writable by us.
        modfilepath = orig_fitspath
    else:
        os.makedirs(moddir, exist_ok=True)
        modfilepath = shutil.copy(orig_fitspath, moddir)
        os.chmod(modfilepath, 0o664)

    logging.debug('new_fits modfilepath={}'.format(modfilepath))
    # Apply changes to header (MODIFY IN PLACE)
    hdulist = pyfits.open(modfilepath, mode='update') # modify IN PLACE
    fitshdr = hdulist[0].header # use only first in list.
    fitshdr.update(changes)
    #hdulist.flush()
    hdulist.close(output_verify='ignore')         # now FITS header is MODIFIED

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
    
    #!md5 = subprocess.check_output("md5sum -b {} | cut -f1 -d' '"
    #!                              .format(fitsfilepath),
    #!                              shell=True)
    #!md5sum=md5.decode().strip()
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
                    persona_options=None,  # e.g. (under "_DTSITE")
                    persona_params=None,   # e.g. (under,under) "__FOO"
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
    options = persona_options if  persona_options else dict()
    opt_params = persona_params if persona_params else dict()
    #!logging.debug('prep_for_ingest(): options={}, opt_params={}'
    #!              .format(options, opt_params))
    
    # +++ API: under-under parameters via lp options
    jidt = opt_params.get('jobid_type',None)  # plain | seconds | (False)
    tag = opt_params.get('job_tag','')
    source = opt_params.get('source','raw')   # pipeline | (dome)
    resubmit = int(opt_params.get('test_resubmit', '0')) # GT 0::try even if HDR exists, ==1::also log error
    logging.debug('resubmit=({})'.format(resubmit))
    # We want "filename" to always be given an option.
    # But we also don't want to force setting of options if we can
    # avoid it. So we use the only fname available: mirror_fname.
    orig_fullname = opt_params.get('filename', mirror_fname)

    #! hdr_ifname = "None"
    hdr=dict()
    try:
        # augment hdr (add fields demanded of downstream process)
        #! hdulist = pyfits.open(mirror_fname, mode='update') # modify IN PLACE
        #! hdr = hdulist[0].header # use only first in list.
        hdr = fu.get_hdr_as_dict(mirror_fname)
        if opt_params.get('OPS_PREAPPLY_UPDATE','no') == 'yes': #!!!
            fu.apply_options(options, hdr)
        if 'DTACQNAM' not in hdr:
            hdr['DTACQNAM'] = orig_fullname
        # we will set DTNSANAM after we generate_fname, here to pass validate
        hdr['DTNSANAM'] = 'NA' 
        fu.validate_raw_hdr(hdr, orig_fullname)
        try:
            fname_fields = fu.fix_hdr(hdr, mirror_fname,
                                      options, opt_params, **kwargs)
            logging.debug('fix_hdr fname_fields={}'.format(fname_fields))
        except Exception as err:
            oldmsg = ('Could not update FITS header of "{}"; {}'
                      .format(orig_fullname, err))
            raise tex.IngestRejection(opt_params, err, hdr)
        fu.validate_cooked_hdr(hdr, orig_fullname)
        if opt_params.get('VERBOSE', False):
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

        #ext = fn.fits_extension(orig_fullname)
        ext = fn.fits_extension(mirror_fname)
        if source == 'pipeline':
            new_basename = hdr['PLDSID'] + ".fits.fz"
            logging.debug('Source=pipeline so using basename:{}'
                          .format(new_basename))
        else:
            new_basename = fn.generate_fname(hdr, ext,
                                             tag=tag,
                                             orig=mirror_fname)
        hdr['DTNSANAM'] = new_basename
        new_ipath = fn.generate_archive_path(hdr, source=source) / new_basename
        #ext = fn.fits_extension(new_basename)
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
        newfits = new_fits(mirror_fname, hdr, moddir=moddir)
        hdrfile = gen_hdr_file(newfits, new_basename)
        iu.irods_put331(hdrfile, new_ihdr)
        os.remove(hdrfile)        
    except Exception as err:
        #!traceback.print_exc()
        #! raise
        #! raise tex.SubmitException('Bad header content in file {}'
        #!                           .format(orig_fullname))
        raise tex.IngestRejection(opt_params, str(err), hdr)

        
    #! iu.irods_put331(mirror_fname, new_ifname) # iput renamed FITS
    #
    # At this point both FITS and HDR are in archive331
    #

    logging.debug('prep_for_ingest: RETURN={}'.format(new_ihdr))
    return new_ihdr, new_ifname, hdr, newfits
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
def submit_to_archive(ifname, checksum, qname, qcfg=None, moddir=None):
    """Ingest a FITS file (really JUST Header) into the archive if
possible.  Ingest involves renaming to satisfy filename
standards. There are numerous under-the-hood requirements imposed by
how Archive works. See comments above for the grim details.

ifname:: full path of fits file (in cache)
checksum:: NOT USED
qname:: Name of queue from tada.conf (e.g. "transfer", "submit")

    """
    logging.debug('submit_to_archive({},{})'.format(ifname, qname))

    
    cfgprms = dict(archive331 =  qcfg['archive_irods331'],
                   mars_host  =  qcfg.get('mars_host'),  
                   mars_port  =  qcfg.get('mars_port'),
                   )

    #!popts, pprms = fu.get_options_dict(ifname + ".options")
    popts, pprms = fu.get_options_dict(ifname) # .yaml or .options
    logging.debug('submit_to_archive(popts={},pprms={})'.format(popts, pprms))
    origfname = pprms.get('filename', ifname)
    try:
        # Following does irods_put331 to new_ihdr if the hdr looks valid
        new_ihdr,destfname,changed,modfits = prep_for_ingest(
            ifname,
            persona_options=popts,
            persona_params=pprms,
            moddir=None,
            **cfgprms)
    except: # Exception as err:
        raise
        #! traceback.print_exc()
    (success, msg, ops_msg, itype) = http_archive_ingest(new_ihdr, qname,
                                                 qcfg=qcfg, origfname=origfname)

    if not success:
        #!rejected = '/var/log/tada/rejected.manifest'
        #!if os.path.exists(rejected):
        #!    with open(rejected, mode='a') as mf:
        #!        print('{}\t{}\t{}'
        #!              .format(datetime.datetime.now(), origfname, destfname),
        #!              file=mf)
        logging.debug(msg)
        if moddir != None:
            os.remove(modfits)
            #!logging.debug('DBG: Removed modfits={}'.format(modfits))
        #raise tex.SubmitException(ops_msg)
        raise tex.IngestRejection(pprms, ops_msg, popts)
    else:
        auditor.log_audit(pprms, success, destfname, ops_msg, popts, changed)

    iu.irods_put331(modfits, destfname) # iput renamed FITS
    if moddir != None:
        os.remove(modfits)
        #!logging.debug('DBG: Removed modfits={}'.format(modfits))
    logging.info('SUCCESSFUL submit_to_archive; {} as {}'
                 .format(origfname, destfname))
    #!manifest = '/var/log/tada/archived.manifest'
    #!if os.path.exists(manifest):
    #!    with open(manifest, mode='a') as mf:
    #!        print('{}\t{}\t{}'
    #!              .format(datetime.datetime.now(), origfname, destfname),
    #!              file=mf)
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
        errmsg = 'Cannot ingest non-FITS file: {}'.format(fitsfile)
        logging.error(errmsg)
        pprms = dict(filename = fitsfile,  md5sum = md5(fitsfile))
        auditor.log_audit(pprms, False, '', errmsg, dict(), dict())
        return (False, errmsg)

    cfgprms = dict(archive331 =  qcfg['archive_irods331'],
                   mars_host  =  qcfg.get('mars_host'),
                   mars_port  =  qcfg.get('mars_port'),
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
        new_ihdr, destfname, changed, modfits = prep_for_ingest(fitsfile,
                                                       persona_options=popts,
                                                       persona_params=pprms,
                                                       moddir=moddir,
                                                       **cfgprms)
    except Exception as err:
        if trace:
            traceback.print_exc()
        msg = str(err)
        logging.error(msg)
        auditor.log_audit(pprms, False, '', str(err), popts, dict())
        return (False, msg)

    success, m1, ops_msg, itype = http_archive_ingest(new_ihdr, qname,
                                               qcfg=qcfg, origfname=origfname)
    auditor.log_audit(pprms, success, destfname, ops_msg, popts, changed)
    if not success:
        if moddir != None:
            os.remove(modfits)
            #!logging.debug('DBG: Removed modfits={}'.format(modfits))
        return(False, 'FAILED: {} not archived; {}'.format(fitsfile, ops_msg))
    else:
        # iput renamed, modified FITS
        iu.irods_put331(modfits, destfname) # iput renamed FITS
        if moddir != None:
            os.remove(modfits)
            #!logging.debug('DBG: Removed modfits={}'.format(modfits))
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
        errmsg = 'Cannot ingest non-FITS file: {}'.format(fitsfile)
        logging.error(errmsg)
        pprms = dict(filename = fitsfile,  md5sum = md5(fitsfile))
        auditor.log_audit(pprms, False, '', errmsg, dict(), dict())
        sys.exit(errmsg)
        
    success = True
    statuscode = 0    # for sys.exit(statuscode)
    statusmsg = 'NA'
    cfgprms = dict(#mirror_dir =  qcfg[qname]['mirror_dir'],
                   archive331 =  qcfg['archive_irods331'],
                   mars_host  =  qcfg.get('mars_host'),
                   mars_port  =  qcfg.get('mars_port'),
                   )

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
        new_ihdr,destfname,changed,modfits = prep_for_ingest(fitsfile,
                                                     persona_options=popts,
                                                     persona_params=pprms,
                                                     moddir=moddir,
                                                     **cfgprms)
    except Exception as err:
        if trace:
            traceback.print_exc()
        statusmsg = str(err)
        #statusmsg = err.errmsg
        success = False
        statuscode = 1
        sys.exit(statusmsg)

        
    success,m1,ops_msg,itype = http_archive_ingest(new_ihdr, qname,
                                         qcfg=qcfg, origfname=origfname)
    auditor.log_audit(pprms, success, destfname, ops_msg, popts, changed)
    if not success:
        statusmsg = 'FAILED: {} not archived; {}'.format(fitsfile, ops_msg)
        statuscode = 2
    else:
        #!iu.irods_put331(newfile, destfname) # iput renamed FITS
        # iput renamed, modified FITS
        iu.irods_put331(modfits, destfname) # iput renamed FITS

        statusmsg= 'SUCCESS: archived {} as {}'.format(fitsfile, destfname)
        statuscode = 0

    print(statusmsg, file=sys.stderr)
    if moddir != None:
        os.remove(modfits)
        #!logging.debug('DBG: Removed modfits={}'.format(modfits))
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
    qcfg, dirs = config.get_config(None,
                                   validate=False,
                                   yaml_filename=args.config)

    direct_submit(args.fitsfile, args.moddir,
                  personality_files=pers_list,
                  trace=args.trace,
                  qcfg=qcfg
                  )
    
if __name__ == '__main__':
    main()


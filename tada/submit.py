"""New TADA to use within NATICA prototype. Uses new Ingest service.
Validate input FITS (valid per TADA pre-personality). 
Copy valid FITS to cache. 
Apply personality to FITS in cache.
Ingest into Archive via web-service.
Remove cache FITS on success, else move to anticache.
"""

import sys
import argparse
import logging
import shutil
import os
import magic
import yaml
import hashlib
from pathlib import PurePath
import collections
import socket

import astropy.io.fits as pyfits
import requests
import errno


from . import exceptions as tex
from . import tada_settings as ts
from . import audit
import tada.hdrfunclib.hdr_funcs as hf

##############################################################################

auditor = audit.Auditor()

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: 
        if e.errno != errno.ENOENT: 
            raise # re-raise exception if a different error occurred

def force_move(src_file, dest_dir):
    dest_file = str(PurePath(dest_dir,PurePath(src_file).name))
    silentremove(dest_file)
    shutil.move(src_file, dest_file)

def force_copy(src_file, dest_dir):
    dest_file = str(PurePath(dest_dir,PurePath(src_file).name))
    silentremove(dest_file)
    shutil.copyfile(src_file, dest_file)
        
# +++ Add code here if TADA needs to handle additional types of files!!!
#!def file_type(filename):
#!    """Return an abstracted file type string.  MIME isn't always good enough."""
#!    type = 'UNKNOWN'
#!    if magic.from_file(filename).find('FITS image data') >= 0:
#!        type = 'FITS'
#!    elif magic.from_file(filename).find('JPEG image data') >= 0:
#!        type = 'JPEG'
#!    elif magic.from_file(filename).find('script text executable') >= 0:
#!        type = 'shell script'
#!    return type


def hdudictlist(fitsfile):
    hdulist = pyfits.open(fitsfile)
    for hdu in hdulist:
        hdu.verify('fix')
    return [collections.OrderedDict(hdu.header.items()) for hdu in hdulist]

def flat_hdudict(fitsfile):
    """Combine key/value pairs from all HDUs into a single dict (returned).
    If key appears in multiple HDUs, first one wins."""
    hdulist = pyfits.open(fitsfile)
    hdudict = dict()
    for hdu in hdulist:
        hdu.verify('fix')
        for k,v in hdu.header.items():
            if k not in hdudict:
                hdudict[k] = v
    return hdudict

##############################################################################

#!def validate_original_fits(fitsfilepath):
#!    """Raise exception if we can tell that FITSFILEPATH does not represent a 
#!FITS file that is valid to ingest into Archive."""
#!    assert 'FITS' == file_type(fitsfilepath)

def get_personality(pers_file):
    """RETURN: python object containing content of personality_file.yaml"""
    #! validate personality file (wrt JSON schema), raise if invalid
    with open(pers_file) as yy:
        yd = yaml.safe_load(yy) # raise Exception if yaml doesn't exist
    logging.debug('get_personality({})'.format(pers_file))
    return yd

def apply_personality(srcfits, destfits, persdict):
    """Use personality file in FITS dir (read into PERSDICT) to transform
SRCFITS to DESTFITS."""

    #origfname = persdict['params']['filename']
    #!hdulist = pyfits.open(srcfits)
    hdu0dict = flat_hdudict(srcfits)
    #!logging.debug('DBG: srcfits ({}) hdulist={}'.format(srcfits, hdu0dict))

    # Apply personality changes
    changed = set()
    for k,v in persdict['options'].items():
        #!logging.debug('apply_personality {}={}'.format(k,v))
        # overwrite with explicit fields from personality
        hdu0dict[k] = v  
        #!changed.add(k) # @@@ disabled because not using hdulist[0].header directly
    # DB uses lowercase for all Telescopes and Instruments
    hdu0dict['DTTELESC'] = hdu0dict['DTTELESC'].lower()
    hdu0dict['DTINSTRU'] = hdu0dict['DTINSTRU'].lower()

    ##########################
    ## Apply "Header Functions" (programatic transformations to FITS hdr).
    ##
    calc_param = persdict['params'].get('calchdr',None)
    calc_funcs = []
    if calc_param != None:
        for funcname in calc_param:
            try:
                func = eval('hf.'+funcname)
                calc_funcs.append(func)
            except:
                raise tex.BadHdrFunc(
                    'Function name "{}" given in option "calchdr"'
                    ' does not exist in tada/hdrfunclib/hdr_funcs.py'
                    .format(funcname))
        # Apply hdr funcs
        #!logging.debug('Apply personality to  hdu0dict={}'.format(hdu0dict))
        for calcfunc in calc_funcs:
            new = calcfunc(hdu0dict)
            logging.info('Ran hdrfunc: {}=>{}'.format(calcfunc.__name__, new))
            hdu0dict.update(new)
    
    ## Write transformed FITS
    silentremove(destfits)
    #!hdulist = pyfits.open(srcfits)
    with pyfits.open(srcfits) as hdulist:
        hdulist[0].header.update(hdu0dict)
        hdulist.writeto(destfits, output_verify='fix')
    #!logging.debug('Applied personality {}({}) => {}; hdu0dict={}'
    #!              .format(srcfits, persdict, destfits, hdu0dict)) # BIG@@@
    return dict(persdict['params'].items())

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

        
def http_archive_ingest(modifiedfits, ingestparams):
    """Deliver FITS to NATICA webservice for ingest."""
    #urls = 'http://0.0.0.0:8000/natica/store/'
    urls = ('http://{host}:{port}/natica/store/{source}/'
            .format(host=ts.natica_host,
                    port=ts.natica_port,
                    source=ingestparams.get('source',None),
            ))
    logging.debug('http_archive_ingest: urls={}, modifiedfits={}, ingestprms={}'
                  .format(urls, modifiedfits, ingestparams))
    md5sum=ingestparams.get('md5sum',md5(modifiedfits))
    source=ingestparams.get('source','dome')
    #! if ingestparams.get('overwrite',False):
    #!     # used to avoid "accidental" use of OVERWRITE in URL. Less important
    #!     # when used in form-encoded data.
    #!     ingestparams['overwrite'] = 13  
    formdict = ingestparams.copy()

    r = requests.post(urls,
                      #! params=ingestparams,      # URL query string
                      #! data=dict(md5sum=md5sum),
                      data=formdict, # form-encoded data for POST
                      files={'fitsfname': open(modifiedfits, 'rb')})
    logging.debug('http_archive_ingest: {}, {}'.format(r.status_code,r.json()))
    return (r.status_code, r.json())

def submit_to_archive(fitspath,
                      personality_yaml=None, #default to buddy of fitspath
                      overwrite=False,
                      cachedir='/var/tada/cache',
                      anticachedir='/var/tada/anticache'):
    """Ingest a FITS file into the archive if possible.  Involves renaming to 
satisfy filename standards. Called directly from DQ Action.

fitspath:: full path of original fits file (in cache). There must be a 
    personality file in <fitspath>.yaml to be used to modify FITS.

personality_yaml :: "options" (fields) and "params" to use for this FITS file
    Defaults to <fitspath>.yaml

overwrite :: Overwrite DB data and FITS file (in archive)

cachedir :: Location for modified FITS (personality applied) before passing
    to ingest serivce.

anticachedir :: Location to store modified FITS if ingest fails.

    """
    logging.debug('submit_to_archive: fitspath={}'.format(fitspath))
    #!validate_original_fits(fitspath) # raise on invalid

    ####################
    ## Apply personality to FITS in-place (roughly "prep_for_ingest")
    ##
    if personality_yaml == None:
        personality_yaml = fitspath+'.yaml'
    persdict = get_personality(personality_yaml)
    inparams = persdict['params'] #INgestPARAMeters: use for ingest of this file
    inparams.setdefault('source','dome')
    if overwrite:
        inparams['overwrite'] = overwrite 
    md5sum = inparams.get('md5sum')
    auditor.set_fstop(md5sum, 'valley:cache')
    fitscache = str(PurePath(cachedir,
                             md5sum + ''.join(PurePath(fitspath).suffixes)))
    try:
        apply_personality(fitspath, fitscache, persdict)
    except tex.BaseTadaException as bte:
        reason = bte.error_message
        auditor.update_audit(md5sum, dict(success=False, reason=reason))
        return False, reason
    except Exception as ex:
        auditor.update_audit(md5sum, dict(success=False, reason=str(ex)))
        return False, str(ex)
    
    #########
    ## ingest via NATICA service
    ##
    (status,jmsg) = http_archive_ingest(fitscache, inparams) #####
    if status == 200:  # SUCCESS
        # Remove cache files; FITS + YAML
        #!logging.warning('NOT removing cache:{}'.format(fitscache))
        os.remove(fitscache) 

        logging.debug('Ingest SUCCESS: {}; {}'.format(fitspath, jmsg))
        auditor.update_audit(md5sum, dict(success=True))
    else:  # FAILURE
        # move FITS + YAML on failure
        force_copy(personality_yaml, anticachedir)
        force_move(fitscache, anticachedir)
        logging.debug('Ingest failed, moved {},{} => {}'
                      .format(personality_yaml,fitscache, anticachedir))
        auditor.update_audit(md5sum,
                             dict(success=False, reason=jmsg['errorMessage']))
        return False, jmsg

    return True, jmsg
    # END: submit_to_archive()
    


##############################################################################

# On archive:
# cd /sandbox/natica/tada
# testfile=/data/tada-test-data/short-drop/20141220/wiyn-whirc/obj_355.fits.fz
# python3 tada.py $testfile
testfile='/data/tada-test-data/short-drop/20141220/wiyn-whirc/obj_355.fits.fz'
def main():
    "Parse command line arguments and do the work."
    #!print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Apply personality modification to FITS. Ingest with NATICA',
        epilog='EXAMPLE: %(prog)s  --loglevel DEBUG {}'.format(testfile),
        formatter_class=argparse.RawTextHelpFormatter
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('fitsfile', type=argparse.FileType('r'),
                        help='FITS file to ingest into Archive')
    parser.add_argument('--overwrite',
                        action='store_true',
                        help='Overwrite file if it already exists in archive')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.fitsfile.close()
    args.fitsfile = args.fitsfile.name

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    status,jmsg = submit_to_archive(args.fitsfile, overwrite=args.overwrite)
    print('Submit results: status={}, msg={}'.format(status,jmsg))

if __name__ == '__main__':
    main()

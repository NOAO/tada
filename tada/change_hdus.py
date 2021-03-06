#! /usr/bin/env python3
"""Modify HDU of FITS file from YAML of hdr name/value pairs.
(from "change_hdr.py")
"""
# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging
#import magic
import os.path
from pathlib import PurePath
import subprocess
import shutil
from pprint import pformat

import astropy.io.fits as pyfits
import yaml
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning

example_YAML_content='''
- _hdu: 0
  DTINSTRU: mosaic3
  DTSITE: kp
  DTTELESC: kp4m
- _hdu: 1
  PROPID: 2016A-0023
  DATE-OBS: "2016-08-18T02:22:07.0"
  '''



def apply_changes(fitsfile, updates_yaml):
    """The work-horse function."""

    with open(updates_yaml) as yy:
        yd = yaml.safe_load(yy)
    
    hdulist = pyfits.open(fitsfile, mode='update') # modify IN PLACE
    for hdudict in yd:
        hdu = int(hdudict['_hdu'])
        del hdudict['_hdu']
        fitshdr = hdulist[hdu].header
        logging.debug('apply_changes: {}'.format(pformat(hdudict)))
        fitshdr.update(hdudict)
    hdulist.close(output_verify='fix')         # now FITS header is MODIFIED
    return None



##############################################################################

def main():
    "Parse command line arguments and do the work."
    #!print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Modify HDUs of FITS file from YAML containing '
        'hdr keyword name/value pairs.',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.1.1')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input FITS file')
    parser.add_argument('outfile', help='Output FITS file')

    parser.add_argument('changes', type=argparse.FileType('r'),
                        help='Input YAML file containing new FITS '
                        'hdr name/value pairs')


    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.infile.close()
    args.infile = args.infile.name
    args.changes.close()
    args.changes = args.changes.name

    #!print 'My args=',args
    #!print 'infile=',args.infile

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    shutil.copyfile(args.infile, args.outfile)
    apply_changes(args.outfile, args.changes)

if __name__ == '__main__':
    main()

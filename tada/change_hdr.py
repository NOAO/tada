#! /usr/bin/env python3
"""Modify header of FITS file from YAML of hdr name/value pairs.
"""
# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging
import magic
import os.path
from pathlib import PurePath
import subprocess
import shutil

import astropy.io.fits as pyfits
import yaml
from astropy.utils.exceptions import AstropyWarning, AstropyUserWarning



def apply_changes(fitsfile, updates_yaml):
    """The work-horse function."""

    with open(updates_yaml) as yy:
        yd = yaml.safe_load(yy)
    
    hdulist = pyfits.open(fitsfile, mode='update') # modify IN PLACE
    fitshdr = hdulist[0].header # use only first in list.
    fitshdr.update(yd)
    hdulist.close(output_verify='fix')         # now FITS header is MODIFIED
    return None



##############################################################################

def main():
    "Parse command line arguments and do the work."
    #!print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Modify header of FITS file from YAML containing '
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

#! /usr/bin/env python3
"""This file is ONLY as an aid to testing.  Not used in production TADA.

The files generated will be valid FITS, but not valid to Archive
Ingest. They should go through TADA, but fail on submit.

Each file is 5760 bytes.  
Took  14 seconds to create  10,000 files (on chimp16).
Took 148 seconds to create 100,000 files (on chimp16).

"""

import sys
import argparse
import logging

import os.path
import astropy.io.fits as pyfits
import datetime

def gen_unique_fits(fitsfile):
    dt = datetime.datetime.now()
    n = [dt.year, dt.month, dt.day,
         dt.hour, dt.minute, dt.second, dt.microsecond]
    hdu = pyfits.PrimaryHDU(n)
    hdu.writeto(fitsfile)


def create_files(outdir, count):
    for num in range(count):
        gen_unique_fits(os.path.join(outdir,'f{:0>6}.fits'.format(num)))


##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('outdir', 
                        help='Write a bunch of FITS files into this dir')
    parser.add_argument('-c', '--count', type=int, default=1,
                        help='Number of FITS files to create')
    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    create_files(args.outdir, args.count)

if __name__ == '__main__':
    main()
    

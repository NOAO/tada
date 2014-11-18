#! /usr/bin/env python
"""<<Python script callable from command line.  Put description here.>>
"""
# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging
import pyfits

from . import fits_utils as fu

def ingest(fname):
    logging.error('Executing STUB: {}.ingest_stub'.format(__file__))
    
def stuff_into_irods(fname):
    logging.error('Executing STUB: {}.stuff_into_irods'.format(__file__))
    
def submit_to_archive(fname):
    "Ingest a FITS file into archive, or stash it in Mitigation queue."
    new_fname = fu.molest(fname)
    logging.debug('post molest fname: {}'.format(new_fname))
    successP,message = fu.valid_header(fname)
    if not successP:
        raise Exception('Invalid FITS header. {}'.format(message))

    stuff_into_irods(fname)
    ingest(fname)
    return new_fname




##############################################################################

def main():
    "Parse command line arguments and do the work."
    print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input file')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='Output output')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    #!args.outfile.close()
    #!args.outfile = args.outfile.name

    #!print 'My args=',args
    #!print 'infile=',args.infile

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    submit(args.infile)

if __name__ == '__main__':
    main()

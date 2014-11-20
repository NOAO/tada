#! /usr/bin/env python
"""<<Python script callable from command line.  Put description here.>>
"""
# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging
import pyfits
import os, os.path

from . import fits_utils as fu
from dataq import dqutils as du
from dataq import irods_utils as iu

def stuff_into_irods(fname, iname):
    logging.debug('Registering {} to {} prior to ingest'.format(fname, iname))
    iu.irods_reg(fname, iname)

def archive_ingest(fname):
    'Touch-point for archive ingest. Stub!!!'
    import random #!!! only needed for mockup
    import inspect

    logging.debug('Executing STUB: {}:archive_ingest()'.format(__file__))
    prop_fail = 0.60
    if random.random() <= prop_fail:  #!!! remove
        logging.debug('Simulated FAILURE [p(Fail)={}] on archive_ingest({})'
                      .format(prop_fail, fname))
        raise Exception('Failed archive_ingest for unknown reason'
                        .format(fname))
    else:
        logging.debug('Simulated SUCCESS [p(Fail)={}] on archive_ingest({})'
                        .format(prop_fail, fname))
    return True
    

# Entry point to archive
#
# Problem: We need to change the filename to reflect naming
# standard. Ingest requires the new name be registered and to be on
# the local file system.  But if something goes wrong, we want the old
# name back. (reverse the side-effect of the name change) We will NOT
# reverse the side-effect of header modification.  We don't want to
# COPY (instead of MOVE) the file since it could be big.
def submit_to_archive(fname, archive_root):
    "Ingest a FITS file into archive, or stash it in Mitigation queue."
    irods_archive_root = '/tempZone/archive/' #!!!
    mo_fname = fu.molest(fname)
    new_fname = os.path.join(os.path.dirname(fname), mo_fname)
    os.rename(fname, new_fname)
    logging.debug('Modified header of fname: {}'.format(new_fname))

    successP,message = fu.valid_header(new_fname)
    if not successP:
        raise Exception('Invalid FITS header. {}'.format(message))

    iname = du.mirror_path(archive_root, new_fname, irods_archive_root)
    stuff_into_irods(new_fname, iname) # makes this func not idempotent? !!!
    try:
        archive_ingest(new_fname)
    except:
        logging.debug('Undo the name change: {} => {}'
                      .format(new_fname, fname))
        os.rename(new_fname, fname)
        return fname
    
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

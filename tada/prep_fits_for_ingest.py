#! /usr/bin/env python
"Intended for use by irods iexecmd.  Adds hdr fields and renames ipath of fits stored in irods"

import os, sys, string, argparse, logging
import tempfile

import pyfits
from . import fits_utils as fu
from . import file_naming as fn
from dataq import irods_utils as iu

def inside_irods_prep(fits_fname, fits_ifname):
    """For use by irods iexecmd. Executes on the same machine as the irods
server.
GIVEN: FITS local file name and irods path
DO: Augment hdr. Rename FITS to satisfy standards. Add hdr as text file irods.
RETURN: (and print) irods location of hdr file.
    """
    hdulist = pyfits.open(fits_fname, mode='update') # modify IN PLACE
    hdr = hdulist[0].header # use only first in list.

    fu.modify_hdr(hdr, fits_fname)
    new_basename = fn.generate_fname(
        instrument=hdr.get('DTINSTRU', 'NOTA'),
        datetime=hdr['OBSID'],
        obstype=hdr.get('OBSTYPE', 'NOTA'),
        proctype=hdr.get('PROCTYPE', 'NOTA'),
        prodtype=hdr.get('PRODTYPE', 'NOTA'),
        )
    #!new_fname  = os.path.join(os.path.dirname(fits_fname ), new_basename)
    new_ifname = os.path.join(os.path.dirname(fits_ifname), new_basename)

    iu.irods_mv(fits_ifname, new_ifname)

    # Create hdr as temp file, i-put, delete tmp file (auto on close)
    hdr_ifname = new_ifname + '.hdr'
    with tempfile.NamedTemporaryFile(mode='w') as f:
        hdr.totextfile(f)
        iu.irods_put(f.name, hdr_ifname)

    hdulist.flush()
    hdulist.close()

    print(hdr_ifname)
    return hdr_ifname


##############################################################################

def main():
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s filename"'
        )
    parser.add_argument('fits_filename',
                        help='Local filesystem path to FITS file',
                        )
    parser.add_argument('irods_filename',
                        help='Full irods path to FITS file',
                        )

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices = ['CRTICAL','ERROR','WARNING','INFO','DEBUG'],
                        default='WARNING',
                        )
    args = parser.parse_args()

    #!print 'My args=',args
    #!print 'infile=',args.infile

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel) 
    logging.basicConfig(level = log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M'
                        )
    logging.debug('Debug output is enabled by nitfConvert!!!')


    inside_irods_prep(args.fits_filename, args.irods_filename)


if __name__ == '__main__':
    main()

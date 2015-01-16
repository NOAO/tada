#! /usr/bin/env python3
"""
OBSOLETE: This approach is problematic because error handling is
more difficult.  Since this defines an executable that irods
executes "remotely", it can not make use of exception handling for
errors.  INSTEAD: find the physical file and work on it directly

##############

Intended for use by irods iexecmd.  Adds hdr fields and renames ipath
of fits stored in irods
"""

import os, sys, string, argparse, logging
import tempfile

#!import pyfits
import astropy.io.fits as pyfits

from . import fits_utils as fu
from . import file_naming as fn
from dataq import irods_utils as iu

def inside_irods_prep(fits_fname, fits_ifname, mirror_idir, archive_idir):
    """For use by irods iexecmd. Executes on the same machine as the irods
server.
GIVEN: FITS local file name and irods path
DO: Augment hdr. Rename FITS to satisfy standards. Add hdr as text file irods.
RETURN: (and print) irods location of hdr file.
    """

    hdr_ifname = "None"
    hdulist = pyfits.open(fits_fname, mode='update') # modify IN PLACE
    hdr = hdulist[0].header # use only first in list.

    try:
        fu.modify_hdr(hdr, fits_fname)
        new_basename = fn.generate_fname(
            instrument=hdr.get('DTINSTRU', 'NOTA'),
            datetime=hdr['OBSID'],
            obstype=hdr.get('OBSTYPE', 'NOTA'),
            proctype=hdr.get('PROCTYPE', 'NOTA'),
            prodtype=hdr.get('PRODTYPE', 'NOTA'),
            )
        new_ifname = os.path.join(os.path.dirname(fits_ifname), new_basename)

        # Create hdr as temp file, i-put, delete tmp file (auto on close)
        hdr_ifname = new_ifname + '.hdr'
        with tempfile.NamedTemporaryFile(mode='w') as f:
            hdr.totextfile(f)
            iu.irods_put(f.name, hdr_ifname)
    except:
        raise
    finally:
        hdulist.flush()
        hdulist.close()

    iu.irods_mv(fits_ifname, new_ifname)
    #imv /tempZone/mountain_mirror/vagrant/11 /tempZone/archive/vagrant/
    origdir = os.path.dirname(new_ifname)
    iu.irods_mv_dir(origdir,
                    os.path.dirname(origdir.replace(mirror_idir, archive_idir)))

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
    parser.add_argument('mirror',
                        help='Root of irods path for mountain mirror',
                        )
    parser.add_argument('archive',
                        help='Root of irods path for archive',
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


    inside_irods_prep(args.fits_filename, args.irods_filename,
                      args.mirror, args.archive)



if __name__ == '__main__':
    main()

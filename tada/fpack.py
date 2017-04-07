#! /usr/bin/env python
"""Lossless fpack.  The default options for floating point fpack
result in lossy compression. Use FITS header info to choose options to
insure lossless compression in all cases.
"""

import logging
import subprocess
import os.path
import shutil
import sys
import argparse
import logging

from . import fits_utils as fu


def remove_if_exists(filename):
    try:
        os.remove(filename)
    except:
        pass

def fpack_to(fitsfile, outfile, force=True):
    """Fpack FITSFILE into OUTFILE (or copy if already fpacked).
    If OUTFILE (.fz) already exists, overwrite IFF force=True.
    RETURN: True IFF fpack was run on this invocation.
    """
    # for floating point 
    # $FPACK -Y -g -q 0 ${BASEFILE}.fits
    fpackcmd = '/usr/local/bin/fpack'
    fitscopycmd = '/usr/local/bin/fitscopy'
    logging.debug('fpack_to({}, {})'.format(fitsfile, outfile))
    tmpoutfile = None

    if force==False and os.path.exists(outfile):
        logging.warning('fpack_to: Outfile already exists. Doing nothing. {}'
                        .format(outfile))
        return False
    if fitsfile[-3:] == '.fz':
        logging.debug('fpack_to: FITSfile already *.fz. Copying to: {}'
                      .format(outfile))
        shutil.copy(fitsfile, outfile)
    else: # compress on the fly
        try:
            remove_if_exists(outfile)
            #!subprocess.call([fitscopycmd, fitsfile, outfile])
            subprocess.run([fitscopycmd, fitsfile, outfile], check=True)
            hdr = fu.get_hdr_as_dict(outfile)

            # FPACK BUG workaround.
            # Despite documentation, fpack will not compress in place if file ends with ".fz"
            if outfile[-3:] == '.fz':
                tmpoutfile = outfile + 'z'  # now: *.fits.fzz
                os.rename(outfile, tmpoutfile)

            if (hdr.get('BITPIX',None) == -32
                or hdr.get('BITPIX',None) == -64):
                # is floating point image
                # Default options are lossy. Use lossless options instead.
                #!subprocess.call([fpackcmd, '-C', '-F', '-g', '-q', 0,outfile])
                subprocess.run([fpackcmd, '-C', '-F', '-g', '-q', 0, tmpoutfile],
                               check=True)
            else:
                #!subprocess.call([fpackcmd, '-C', '-F', outfile])
                subprocess.run([fpackcmd, '-C', '-F', tmpoutfile], check=True)

            # FPACK BUG workaround.
            if tmpoutfile:
                os.rename(tmpoutfile, outfile)                

        except subprocess.CalledProcessError as ex:
            logging.error('FAILED fpack_to: {}; returncode={}'
                          .format(ex, ex.returncode))
            raise
    #logging.debug('move to cache ({},{})'.format(tmpfile, outfile))
    #shutil.move(tmpfile, outfile)
    logging.debug('DONE: fpack_to({}, {})'.format(fitsfile, outfile))
    return outfile

##############################################################################

def main():
    "Parse command line arguments and do the work."
    print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='FPACK as used in TADA',
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

    fpack_to(args.infile, args.outfile, force=False)

if __name__ == '__main__':
    main()

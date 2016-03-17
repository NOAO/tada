"""Lossless fpack.  The default options for floating point fpack
result in lossy compression. Use FITS header info to choose options to
insure lossless compression in all cases.
"""

import astropy.io.fits as pyfits
import logging
import subprocess
import os.path

# for floating point
# $FPACK -Y -g -q 0 ${BASEFILE}.fits

def fpack_to(fitsfile, outfile=None, personality=None):
    # /usr/local/bin/fpack -v $fitsfile > $outfile
    tag='fpack_to'
    cmdpath = '/usr/local/bin'
    logging.debug('{}({},{})'.format(tag, fitsfile, outfile))

    logging.warning('Not enforcing lossless compression in "fpack_to"')
    
    try:
        with open(outfile, 'w') as file:
            subprocess.call([os.path.join(cmdpath, 'fpack'), '-S', fitsfile],
                           stdout=file)
    except subprocess.CalledProcessError as ex:
        logging.error('FAILED {}: {}; {}'
                      .format(tag, ex, ex.output.decode('utf-8')))
        raise


"""Lossless fpack.  The default options for floating point fpack
result in lossy compression. Use FITS header info to choose options to
insure lossless compression in all cases.
"""

import logging
import subprocess
import os.path
import shutil

from . import fits_utils as fu


def remove_if_exists(filename):
    try:
        os.remove(filename)
    except:
        pass

def fpack_to(fitsfile, outfile, force=False):
    """Fpack FITSFILE into OUTFILE (or copy if already fpacked).
    If OUTFILE (.fz) already exists, overwrite IFF force=True.
    RETURN: True IFF fpack was run on this invocation.
    """
    # for floating point 
    # $FPACK -Y -g -q 0 ${BASEFILE}.fits
    tag='fpack_to'
    fpackcmd = '/usr/local/bin/fpack'
    logging.debug('{}({},{})'.format(tag, fitsfile, outfile))
    assert outfile[-3:] == '.fz'

    if force==False and os.path.exists(outfile):
        logging.warning('{}: Outfile already exists. Doing nothing.'.
                        format(tag))
        return False
    if fitsfile[-3:] == '.fz':
        logging.debug('{}: FITSfile already *.fz. Copying.'.format(tag))
        shutil.copy(fitsfile, outfile)
        return False

    #ELSE compress on the fly

    try:
        hdr = fu.get_hdr_as_dict(fitsfile)
        remove_if_exists(outfile)
        with open(outfile, 'wb') as file:
            # -S :: Output compressed FITS files to STDOUT.
            if hdr.get('BITPIX',None) == -32 or hdr.get('BITPIX',None) == -64:
                # is floating point image
                # Default options are lossy. Use lossless options instead.
                subprocess.call([fpackcmd, '-C', '-S', '-g', '-q', 0, fitsfile],
                                stdout=file)
            else:
                subprocess.call([fpackcmd, '-C', '-S', fitsfile], stdout=file)
    except subprocess.CalledProcessError as ex:
        logging.error('FAILED {}: {}; {}'
                      .format(tag, ex, ex.output.decode('utf-8')))
        raise
    logging.debug('DONE: {}({},{})'.format(tag, fitsfile, outfile))
    return outfile


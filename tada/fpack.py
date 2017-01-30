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
    fpackcmd = '/usr/local/bin/fpack'
    fitscopycmd = '/usr/local/bin/fitscopy'
    logging.debug('fpack_to({}, {})'.format(fitsfile, outfile))

    #tmpfile = outfile.replace('/cache/','/cache/.tempcache/')
    #os.makedirs(os.path.dirname(tmpfile), exist_ok=True)

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
            subprocess.call([fitscopycmd, fitsfile, outfile])
            hdr = fu.get_hdr_as_dict(outfile)
            #with open(outfile, 'wb') as file:
            # -S :: Output compressed FITS files to STDOUT.
            if (hdr.get('BITPIX',None) == -32
                or hdr.get('BITPIX',None) == -64):
                # is floating point image
                # Default options are lossy. Use lossless options instead.
                subprocess.call([fpackcmd, '-C', '-F', '-g',
                                 '-q', 0, outfile])
            else:
                #!subprocess.call([fpackcmd, '-C', '-S', fitsfile],
                #!                stdout=file)
                subprocess.call([fpackcmd, '-C', '-F', outfile])
        except subprocess.CalledProcessError as ex:
            logging.error('FAILED fpack_to: {}; {}'
                          .format(ex, ex.output.decode('utf-8')))
            raise
    #logging.debug('move to cache ({},{})'.format(tmpfile, outfile))
    #shutil.move(tmpfile, outfile)
    logging.debug('DONE: fpack_to({}, {})'.format(fitsfile, outfile))
    return outfile


"""Diagnostics. 
Nothing here is required for production but use of it would have to be 
commented out before this file could be removed."""

import astropy.io.fits as pyfits
import logging
import collections
import traceback
from glob import glob
from pprint import pprint

def metadata_field_use(fits_filenames):
    "Find Common and Optional sets of fields used in list of fits files."
    if len(fits_filenames) < 2:
        return None, None

    sets = [set(pyfits.open(fname)[0].header.keys())
            for fname in fits_filenames]
    common = sets[0].intersection(*sets[1:])
    allfields = sets[0].union(*sets[1:])
    optional =  allfields - common
    return common, optional

# files = glob("~/fits/*")
def metadata_catalog(fits_filenames):
    "Histogram the metadata values in list of fits files."
    
    common, optional = metadata_field_use(fits_filenames)
    allfields = optional.union(common)
    histo = collections.defaultdict(int)
    values = collections.defaultdict(set)
    for fname in fits_filenames:
        hdulist = pyfits.open(fname)
        hdr = hdulist[0].header
        for field in allfields:
            if field in hdr:
                histo[field] += 1
                values[field].add(str(hdr[field]))
        hdulist.close()

    print('\n', '~'*78)
    print('Histogram of field use:')
    pprint(histo)

    print('\n', '~'*78)
    
    max_unique = 0.80
    print('Values used (max %s unique values):'%(max_unique))
    #! pprint(values)
    for k,v in values.items():
        if float(len(v))/len(fits_filenames) > max_unique: continue
        print('%8s: %s'%(k,', '.join(v)))
            
            
def dbgcmd(cmdargs, msg='EXECUTING cmd: '):
    logging.debug('{}{}'.format(msg,' '.join(cmdargs)))



def traceback_if_debug():
    "Print traceback of logging level is set to DEBUG"
    if logging.DEBUG == logging.getLogger().getEffectiveLevel():
        traceback.print_exc()
    

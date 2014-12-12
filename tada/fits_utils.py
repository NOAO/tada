#! /usr/bin/env python3
"""Fiddling with Fits (tm)"""
import sys
import argparse
import logging


import pyfits
import datetime
import os.path
 
from . import file_naming as fn
from . import exceptions as tex

# common between a SINGLE raw and cooked pair
common_fields = [
    '',
    'AIRMASS',
    'ALT',
    'AZ',
    'BITPIX',
    'DATE-OBS',
    'DEC',
    'DECDIFF',
    'DECINDEX',
    'DECINST',
    'DECOFF',
    'DECZERO',
    'DOMEAZ',
    'DOMEERR',
    'EXPCOADD',
    'EXPID',
    'EXPTIME',
    'EXTEND',
    'FILENAME',
    'FILTER',
    'HA',
    'INSTRUME',
    'LAMPSTAT',
    'MJD-OBS',
    'MOSSIZE',
    'NAXIS',
    'NCOADD',
    'NDETS',
    'NEXTEND',
    'NFC1FILT',
    'NFC1GDR',
    'NFC1POS',
    'NFC2FILT',
    'NFC2GDR',
    'NFC2POS',
    'NFDETTMP',
    'NFECPOS',
    'NFFILPOS',
    'NFFW1POS',
    'NFFW2POS',
    'NFOSSTMP',
    'NOCAOE',
    'NOCBIAS',
    'NOCCOADD',
    'NOCDDOF',
    'NOCDGAVG',
    'NOCDHS',
    'NOCDITER',
    'NOCDPAT',
    'NOCDPOS',
    'NOCDREP',
    'NOCDROF',
    'NOCFOCUS',
    'NOCFSMPL',
    'NOCFSN',
    'NOCID',
    'NOCLAMP',
    'NOCMDOF',
    'NOCMITER',
    'NOCMPAT',
    'NOCMPOS',
    'NOCMREP',
    'NOCMROF',
    'NOCNO',
    'NOCNPOS',
    'NOCNUM',
    'NOCOAE',
    'NOCODEC',
    'NOCORA',
    'NOCPIE',
    'NOCPOST',
    'NOCSCR',
    'NOCSKY',
    'NOCSYS',
    'NOCTIM',
    'NOCTOT',
    'NOCTYP',
    'NOHS',
    'OBJDEC',
    'OBJECT',
    'OBJEPOCH',
    'OBJRA',
    'OBSERVAT',
    'OBSERVER',
    'OBSID',
    'OBSTYPE',
    'PROCTYPE',
    'PROPID',
    'PROPOSER',
    'RA',
    'RADECEQ',
    'RADECSYS',
    'RADIFF',
    'RAINDEX',
    'RAINST',
    'RAOFF',
    'RAZERO',
    'SEQID',
    'SEQNUM',
    'SIMPLE',
    'ST',
    'TCPGDR',
    'TCPTRACK',
    'TELDEC',
    'TELEQUIN',
    'TELESCOP',
    'TELFOCUS',
    'TELOP',
    'TELRA',
    'TELRADEC',
    'TIME-OBS',
    'TIMESYS',
    'ZD']

added_molested_fields = [
    'CHECKSUM',
    'DATASUM',
    'DTACCOUN',
    'DTACQNAM',
    'DTACQUIS',
    'DTCALDAT',
    'DTCOPYRI',
    'DTINSTRU',
    'DTNSANAM',
    'DTOBSERV',
    'DTPI',
    'DTPIAFFL',
    'DTPROPID',
    'DTSITE',
    'DTSTATUS',
    'DTTELESC',
    'DTTITLE',
    'DTUTC',
    'DT_RTNAM',
    'ODATEOBS',
    'RECNO',
    'RMCOUNT',
    'SB_ACCOU',
    'SB_DIR1',
    'SB_DIR2',
    'SB_DIR3',
    'SB_HOST',
    'SB_ID',
    'SB_LOCAL',
    'SB_NAME',
    'SB_RECNO',
    'SB_RTNAM',
    'SB_SITE',
    ]

RAW_REQUIRED_FIELDS = set([
    'DATE-OBS',
    'INSTRUME',
    'OBSERVAT',
    'OBSID',
    'PROPID',
    'PROPOSER',
])
    
INGEST_REQUIRED_FIELDS = set([
    'DATE-OBS',
    'DTACQNAM',
    'DTINSTRU',
    'DTNSANAM',
    'DTPI',
    'DTSITE',
    'DTTELESC',
    'DTTITLE',
    'DTUTC',
    'PROPID',
])


def get_archive_header(fits_file, checksum):
    # Only look at first/primary HDU?!!! (Header Data Unit)
    hdu = pyfits.open(fits_file)[0] # can be compressed
    hdr_keys = set(hdu.header.keys())
    params = dict(filename=fits_file,
                  filesize=os.path.getsize(fits_file),
                  checksum=checksum,
              )
    return """\
#filename = {filename}
#reference = {filename}
#filetype = UNKNOWN
#filesize = {filesize} bytes
#file_md5 = {checksum}

""".format(**params)

    
def valid_header(fits_file):
    """Read FITS metadata and insure it has what we need. 
Raise exception if not."""
    try:
        # Only look at first/primary HDU?!!! (Header Data Unit)
        hdu = pyfits.open(fits_file)[0] # can be compressed
        hdr_keys = set(hdu.header.keys())
    except Exception as err:
        raise tex.InvalidHeader('Metadata keys could not be read: {}'
                                       .format(err))

    missing = sorted(RAW_REQUIRED_FIELDS - hdr_keys)
    if len(missing) > 0:
        raise tex.HeaderMissingKeys(
            'FITS file "{}" is missing required metadata keys: {}'
            .format(fits_file, missing))
    return True


"""    
DTACCOUN= 'cache             '  /  observing account name                    
DTACQNAM= '/home/data/data16923.fits'  /  file name supplied at telescope    
DTACQUIS= 'nfdca-KP.kpno.noao.edu'  /  host name of data acquisition computer
DTCALDAT= '2008-02-24        '  /  calendar date from observing schedule     
DTCOPYRI= 'AURA              '  /  copyright holder of data                  
DTINSTRU= 'newfirm           '  /  instrument identifier                     
DTNSANAM= 'kp680491.fits     '  /  file name in NOAO Science Archive         
DTOBSERV= 'NOAO              '  /  scheduling institution                    
DTPI    = 'Peter Frinchaboy  '  /  Principal Investigator                    
DTPIAFFL= 'University of Wisconsin, Madison'  /  PI affiliation              
DTPROPID= '2007B-0092        '  /  observing proposal ID                     
DTSITE  = 'kp                '  /  observatory location                      
DTSTATUS= 'done              '  /  data transport status                     
DTTELESC= 'kp4m              '  /  telescope identifier                      
DTTITLE = 'WIYN Open Cluster Study (WOCS)'  /  title of observing proposal   
DTUTC   = '                  '  /  post exposure UTC epoch from DTS          
    
SB_DIR1 = '20080224          '  /  level 1 directory in NSA DS               
SB_DIR2 = 'kp4m              '  /  level 2 directory in NSA DS               
SB_DIR3 = '2007B-0092        '  /  level 3 directory in NSA DS               
SB_HOST = 'dtskp.kpno.noao.edu'  /  iSTB client host                         
SB_ID   = 'kp680491          '  /  unique iSTB identifier                    
SB_LOCAL= 'kp                '  /  locale of iSTB daemon                     
SB_NAME = 'kp680491.fits     '  /  name assigned by iSTB                     
SB_RECNO=               680491  /  iSTB sequence number                      
SB_SITE = 'kp                '  /  iSTB host site                            
"""    


# Used istb/src/header.{h,c} for hints.
# raw: nhs_2014_n14_299403.fits
def molest(fits_file):
    """Add fields to hdr and create filename that 
 satisfies http://ast.noao.edu/data/docs"""
    
    hdulist = pyfits.open(fits_file, mode='update') # modify IN PLACE
    hdr = hdulist[0].header

    missing = RAW_REQUIRED_FIELDS - set(hdr.keys())
    if len(missing) > 0:
        raise Exception(
            'Raw fits file "{}" is missing required metadata fields: {}'
            .format(fits_file, ', '.join(sorted(missing)))
            )

    # e.g. OBSID = 'kp4m.20141114T122626'
    tele, dt_str = hdr['OBSID'].split('.')
    date, time = dt_str.split('T')
    dateobs = datetime.datetime.strptime(hdr['DATE-OBS'],'%Y-%m-%dT%H:%M:%S.%f')
    
    hdr['DTACQNAM'] = '' # file name supplied at telescope
    hdr['DTINSTRU'] = hdr['INSTRUME'] # eg. 'NEWFIRM'
    #hdr['DTNSANAM'] = '' #file name in NOAO Science Archive            
    hdr['DTPI']     = hdr['PROPOSER']
    hdr['DTSITE']   = hdr['OBSERVAT'].lower()
    hdr['DTTELESC'] = tele
    hdr['DTTITLE']  = 'Field not derivable from raw metadata!!!',
    # DTUTC cannot be derived exactly from any RAW fields
    hdr['DTUTC']    = dateobs.strftime('%Y-%m-%dT%H:%M:%S') # slightly wrong!!!

    hdr['SB_DIR1'] = date
    hdr['SB_DIR2'] = tele
    hdr['SB_DIR3'] = hdr['PROPID']
    # e.g. SB_DIR1='20141113', SB_DIR2='kp4m', SB_DIR3='2013B-0236'
    
    new_fname = fn.generate_fname(
        instrument=hdr.get('DTINSTRU', 'NOTA'),
        datetime=hdr['OBSID'],
        obstype=hdr.get('OBSTYPE','NOTA'),
        proctype=hdr.get('PROCTYPE','NOTA'),
        prodtype=hdr.get('PRODTYPE','NOTA'),
    )

    hdulist.flush()
    hdulist.close()

    # e.g. "k4k_140923_024819_uri.fits.fz"
    return new_fname




def fits_compliance(fits_file_list):
    """Check FITS file for complaince with Archive Ingest."""
    status = False
    for ffile in fits_file_list:
        valid_header(ffile)
    return(status)



##############################################################################

def main():
    "Parse command line arguments and do the work."
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('infiles',
                        nargs='+',
                        help='Input file')

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

    fits_compliance(args.infiles)

if __name__ == '__main__':
    main()

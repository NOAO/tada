"""Fiddling with Fits"""

import pyfits
import datetime
import logging

from . import file_naming as fn

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


def valid_header(fits_file):
    """Read FITS metadata and insure it has what we need. 
 Return (success, message)."""
    try:
        # Only look at first/primary HDU?!!! (Header Data Unit)
        hdu = pyfits.open(fits_file)[0] # can be compressed
        hdr_keys = set(hdu.header.keys())
    except Exception as err:
        return False, 'Metadata keys could not be read: %s' % err

    missing = sorted(RAW_REQUIRED_FIELDS - hdr_keys)
    if len(missing) > 0:
        return (False,
                'FITS file is missing required metadata keys: %s'
                % (missing,))
    return True, None


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
    logging.debug('generated new_fname: {}'.format(new_fname))

    hdulist.flush()
    hdulist.close()

    # e.g. "k4k_140923_024819_uri.fits.fz"
    return new_fname

def metadata_field_use(fits_filenames):
    "Find Common and Optional sets of fields used in list of fits files."
    if len(fits_filenames) < 2:
        return None, None

    sets = [set(pyfits.open(fname)[0].header.keys())
            for fname in fits_filenames]
    common = sets[0].intersection(*sets[1:])
    all = sets[0].union(*sets[1:])
    optional =  all - common
    return common, optional


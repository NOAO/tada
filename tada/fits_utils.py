#! /usr/bin/env python3
"""Fiddling with Fits (tm)"""

import sys
import argparse
import logging
import traceback


#!import pyfits
import astropy.io.fits as pyfits
import datetime
import os.path
 
from . import file_naming as fn
from . import exceptions as tex

##############################################################################
# Req-A1: set of header keywords required by NSA ingestion per
# "safestore_raw_pixel_data.pdf (Use Case Specification)
#    DTACCOUN observing account name
#    DTACQNAM file name supplied at telescope
#    DTACQUIS host name of data acquisition computer
#    DTCALDAT calendar date from observing schedule
#    DTCOPYRI copyright holder of data
#    DTINSTRU instrument identifier
#    DTNSANAM file name in storage system
#    DTOBSERV scheduling institution
#    DTPI Principal Investigator
#    DTPIAFFL PI affiliation
#    DTPROPID observing proposal ID
#    DTPUBDAT calendar date of public release   #
#    DTSITE observatory location
#    DTTELESC telescope identifier
#    DTTITLE title of obser
##############################################################################

# To be able to ingest a fits file into the archive, all of these must
# be present in the header.
# The commented out lines are Requirements per document, but did not seem to
# be required in Legacy code.
INGEST_REQUIRED_FIELDS = set([
    'DATE-OBS',
#    'DTACCOUN', # observing account name
    'DTACQNAM',
#    DTACQUIS host name of data acquisition computer
#    DTCALDAT calendar date from observing schedule
#    DTCOPYRI copyright holder of data
    'DTINSTRU',
    'DTNSANAM',
#    DTOBSERV scheduling institution
    'DTPI',
#    DTPIAFFL PI affiliation
#    DTPROPID observing proposal ID
#    DTPUBDAT calendar date of public release 
    'DTSITE',
    'DTTELESC',
    'DTTITLE',
    'DTUTC',
    'PROPID',
])



# common between a SINGLE Raw and Cooked pair
#   "Cooked":: contains (at least) added fields required for Archive Ingest
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

# This information was derived from a SINGLE pair of example FITS
# files (corresponding to the file Before and After STB modified the
# header).
#
# Fields added to raw FITS before ingesting. Its unknown which of these
# are strictly required.
added_fields = [
    'CHECKSUM',
    'DATASUM',
    'DTACCOUN', # Req-A1: observing account name
    'DTACQNAM', # Req-A1: file name supplied at telescope
    'DTACQUIS', # Req-A1: host name of data acquisition computer
    'DTCALDAT', # Req-A1: calendar date from observing schedule
    'DTCOPYRI', # Req-A1: copyright holder of data
    'DTINSTRU', # Req-A1: instrument identifier
    'DTNSANAM', # Req-A1: file name in storage system
    'DTOBSERV', # Req-A1: scheduling institution
    'DTPI',     # Req-A1: Principal Investigator
    'DTPIAFFL', # Req-A1: PI affiliation
    'DTPROPID', # Req-A1: observing proposal ID
    'DTPUBDAT', # Req-A1: calendar date of public release  ##
    'DTSITE',   # Req-A1: observatory location
    'DTSTATUS',
    'DTTELESC', # Req-A1: telescope identifier
    'DTTITLE',  # Req-A1: title of obser
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

# All bets are off in the original FITS file does not contain all of these.
RAW_REQUIRED_FIELDS = set([
    'DATE-OBS',
    'INSTRUME',
    'OBSERVAT',
    'OBSID',
    'PROPID',
    # 'PROPOSER', #!!! will use PROPID when PROPOSER doesn't exist in raw hdr
])



def extract_header(fits_filename=None, hdr_filename=None):
    "Get the 'header' from FITS file. Write it to text file."
    if fits_filename == None:
        fits_filename = sys.argv[1]
    if hdr_filename == None:
        hdr_filename = sys.argv[2]

    hdulist = pyfits.open(fits_filename) # ok if is compressed ('fz')
    hdr = hdulist[0].header
    with open(hdr_filename, 'w') as f:
        hdr.totextfile(f)
    
# It seems unconscionably complex for Ingest to require extra lines be
# prepended to the text of the fits header.  The only reason those
# same 5 fields couldn't be added to the header itself is that one of
# them is 9 characters but fits limites field names to 8 characters.
# Once Ingest made the decision to require special non-header fields,
# it should have just defined exactly what it needed (not prepended);
# including defining what is optional.  There is no published
# "contract" for what exactly should be sent to Ingest via TCP!
def get_archive_header(fits_file, checksum):
    "Get the 'header' that archive ingest wants to see sent to it over TCP"
    # Only look at first/primary HDU?!!! (Header Data Unit)
    hdu = pyfits.open(fits_file)[0] # can be compressed
    hdr_keys = set(hdu.header.keys())
    params = dict(filename=fits_file,
                  filesize=os.path.getsize(fits_file),
                  checksum=checksum,
                  hdr=dhu.header,
              )
    return """\
#filename = {filename}
#reference = {filename}
#filetype = UNKNOWN
#filesize = {filesize} bytes
#file_md5 = {checksum}

{hdr}
""".format(**params)

def missing_in_hdr(hdr, required_fields):
    hdr_keys = set(hdr.keys())
    missing = sorted(required_fields - hdr_keys)
    return missing

def missing_in_raw_hdr(hdr):
    """Header from original FITS input to TADA doesn't contain minimum
 acceptable fields."""
    return missing_in_hdr(hdr, RAW_REQUIRED_FIELDS)

def missing_in_archive_hdr(hdr):
    """Header from FITS oesn't contain minimum fields acceptable for
 Archive Ingest."""
    return missing_in_hdr(hdr, INGEST_REQUIRED_FIELDS)

def valid_header(fits_file):
    """Read FITS metadata and insure it has what we need. 
Raise exception if not."""
    try:
        # Only look at first/primary HDU?!!! (Header Data Unit)
        hdulist = pyfits.open(fits_file) # can be compressed
        hdr = hdulist[0].header
    except Exception as err:
        raise tex.InvalidHeader('Metadata keys could not be read: {}'
                                       .format(err))
    missing = missing_in_raw_hdr(hdr)
    if len(missing) > 0:
        raise tex.HeaderMissingKeys(
            'Missing required metadata keys: {}'
            .format(missing))
    return True



# EXAMPLE compliant header (included here for descriptions):
"""    
SIMPLE  =                    T / File conforms to FITS standard                 
BITPIX  =                    8 / Bits per pixel (not used)                      
NAXIS   =                    0 / PHU contains no image matrix                   
EXTEND  =                    T / File contains extensions                       
NEXTEND =                    2 / Number of extensions                           
FILENAME= 'n3.09786.fits'      / Original host filename                         
OBJECT  = 'SkyFlat Blue'       / Observation title                              
OBSTYPE = 'flat    '           / Observation type                               
OBSMODE = 'sos_slit'           / Observation mode                               
EXPTIME =                   20 / Exposure time (sec)                            
RADECSYS= 'FK5     '           / Default coordinate system                      
RADECEQ =                2000. / Default equinox test4                          
RA      = '18:12:45.72'        / RA of observation (hr)                         
DEC     = '31:57:45.0'         / DEC of observation (deg)                       
OBJRA   = '18:12:45.72'        / Right Ascension                                
OBJDEC  = '31:57:45.0'         / Declination                                    
OBJEPOCH=               2014.7 / [yr] epoch                                     
TIMESYS = 'UTC approximate'    / Time system                                    
DATE-OBS= '2014-09-22T01:35:48.0'  /  UTC epoch                                 
TIME-OBS= '1:35:48 '           / Universal time                                 
MJD-OBS =       56922.06652778 / MJD of observation start                       
ST      = '18:13:55'           / Sidereal time                                  
MJDSTART=      56922.066558066 / MJD of observation start                       
MJDEND  =      56922.067317367 / MJD of observation end                         
OBSERVAT= 'KPNO    '           / Observatory                                    
TELESCOP= 'KPNO 4.0 meter telescope' / Telescope                                
TELRADEC= 'FK5     '           / Telescope coordinate system                    
TELEQUIN=               2014.7 / Equinox of tel coords                          
TELRA   = '18:12:45.72'        / RA of telescope (hr)                           
TELDEC  = '31:57:45.0'         / DEC of telescope (deg)                         
HA      = '0:00:00.00'         / Telescope hour angle                           
ZD      =                    0 / Zenith distance                                
AIRMASS =                    1 / Airmass                                        
INSTRUME= 'KOSMOS  '           / Kosmos detector                                
DETSIZE = '[1:2048,1:4096]'    / Kosmos detector size                           
NDETS   =                    1 / Number of detectors in kosmos                  
FILTER  = 'Open    '           / Filter                                         
DISPERSR= 'b2k kb2k'           / Disperser                                      
SLITWHL = '4pxB k4pxB'         / Slit Wheel                                     
DEWAR   = 'KOSMOS Dewar'       / Dewar identification                           
OBSERVER= 'Hirschauer, Salzer' / Observer(s)                                    
PROPOSER= 'John Salzer'        / Proposer(s)                                    
PROPID  = '2014B-0461'         / Proposal identification                        
OBSID   = 'kp4m.20140922T013548' / Observation ID                               
EXPID   =                    0 / Monsoon exposure ID                            
NOCID   =      2456922.7748827 / NOCS exposure ID                               
DHEFILE = 'kosmos_e2v_Sequencer_roiV206.ucd' / Sequencer file                   
NOCROIRZ=                    0 / Detector ROI row size                          
NOCDEVIC= 'e2v     '           / Detector device                                
NOCOFFG = '0.0 0.0 '           / ntcs_gdroffset x y offset (mm)                 
NOCNO   =                    1 / observation number in this sequence            
NOCGAIN = 'unknown '           / Controller gain                                
NOCDFIL =                    0 / Dither offsets file                            
NOCDHS  = 'STFLAT  '           / DHS script name                                
NOCGPXPS=                    0 / Monsoon pixel row/column shift                 
NOCFSTEP=                    0 / [um] step value for focus adjustments          
NOCSLEW = '00:00:00.00 00:00:00.0 2010' / ntcs_moveto ra dec epoch              
NOCFITER=                    0 / Number of focus positions                      
NOCCSN  = 'kHeNeAr '           / Calibration lamp serial number                 
NOCTOT  =                    1 / Total number of observations in set            
NOCSCR  = 'STFLAT  '           / NOHS script run                                
NOCTIM  =                   20 / [s] Requested integration time                 
NOCOFFT = '0.0 0.0 '           / ntcs_offset RA Dec offset (arcsec)             
NOCROIPT= 'FullFrame'          / Detector ROI pattern (FullFrame|4kx2k|4kx300|2k
NOCSYS  = 'kpno 4m '           / system ID                                      
NOCNUM  =                    1 / observation number request                     
NOCLAMP = 'off     '           / Dome flat lamp status (on|off|unknown)         
NOCRBIN =                    1 / CCD row binning                                
NOCROICS=                    0 / Detector ROI colum start                       
NOCNPOS =                    1 / observation number in requested number         
NOCROI  = 'disabled'           / Detector ROI flag (enabled|disabled)           
NOCCBIN =                    1 / CCD column binning                             
NOCTYP  = 'FLAT    '           / Observation type (zero|dark|flat|arc|focus|acq|
NOCPOST = 'sky     '           / Calibration position (unknown|init|sky|dfs|lamp
NOCDPOS =                    0 / Dither position                                
NOCROICZ=                    0 / Detector ROI column size                       
NOCROIRS=                    0 / Detector ROI row start                         
NOCCAL  = 'HeNeAr  '           / Calibration lamp                               
NOCDPAT = 'unknown '           / Dither pattern                                 
RAZERO  =               -36.13 / [arcsec] RA zero                               
RAINDEX =                    0 / [arcsec] RA index                              
ALT     = '90:00:00.0'         / Telescope altitude                             
DECINST =                    0 / [arcsec] Dec instrument center                 
DECDIFF =                    0 / [arcsec] Dec diff                              
PARALL  =                  360 / [deg] parallactic angle                        
RADIFF  =                    0 / [arcsec] RA diff                               
DECZERO =                61.25 / [arcsec] Dec zero                              
AZ      = '0:00:00.0'          / Telescope azimuth                              
RAINST  =                    0 / [arcsec] RA instrument center                  
DECOFF  =                    0 / [arcsec] Dec offset                            
DECINDEX=                    0 / [arcsec] Dec index                             
RAOFF   =                    0 / [arcsec] RA offset                             
GCCROTAT=            90.199997 / [Degrees] Instrument rotator angle             
KSDPOS  = 'b2k     '           / actual name {between|lo|med|high|narrow|other|o
KSDWPOS =                    6 / wheel actual pos {0|1|2|3|4|5|6}               
KSFILCMD= 'Open    '           / actual name {between|U|B|V|R|I|open}           
KSFW1POS=                    2 / wheel 1 actual pos {0|1|2|3|4|5|6}             
KSFW2POS=                    1 / wheel 2 actual pos {0|1|2|3|4|5|6}             
KSSWPOS =                    2 / wheel actual pos {0|1|2|3|4|5|6}               
KSSPOS  = '4pxB    '           / actual name {between|long|1px|2px|narrow|other|
KSCAMFOC=           1849.97998 / [um] camera focus                              
KSCAMZRO=                 1850 / [um] camera focus zeropoint                    
DOMEERR =                    0 / [deg] Dome error as distance from target       
DOMEAZ  =                    0 / [deg] Dome position                            
KSTEMP1 =                 23.6 / [Celsius] temperature sensor 1                 
KSTEMP2 =                 18.9 / [Celsius] temperature sensor 2                 
KSTEMP3 =                 18.8 / [Celsius] temperature sensor 3                 
KSTEMP4 =                 18.1 / [Celsius] temperature sensor 4                 
KSCOLFOC=           499.980011 / [um] collimator focus                          
KSCOLZRO=                  500 / [um] collimator focus zeropoint                
DTSITE  = 'kp                '  /  observatory location                         
DTTELESC= 'kp4m              '  /  telescope identifier                         
DTINSTRU= 'kosmos            '  /  instrument identifier                        
DTCALDAT= '2014-09-21        '  /  calendar date from observing schedule        
ODATEOBS= '                  '  /  previous DATE-OBS                            
DTUTC   = '2014-09-22T01:37:04'  /  post exposure UTC epoch from DTS            
DTOBSERV= 'NOAO              '  /  scheduling institution                       
DTPROPID= '2014B-0461        '  /  observing proposal ID                        
DTPI    = 'John Salzer       '  /  Principal Investigator                       
DTPIAFFL= 'Indiana University'  /  PI affiliation                               
DTTITLE = 'Spectroscopy of Ultra-Low Metallicity Star-Forming Galaxies'  /  titl
DTCOPYRI= 'AURA              '  /  copyright holder of data                     
DTACQUIS= 'kosmosdhs-4m.kpno.noao.edu'  /  host name of data acquisition compute
DTACCOUN= 'cache             '  /  observing account name                       
DTACQNAM= '/home/data/n3.09786.fits'  /  file name supplied at telescope        
DTNSANAM= 'k4k_140922_013704_fri.fits'  /  file name in NOAO Science Archive    
DT_RTNAM= 'k4k_140922_013704_fri'  /  NSA root name                             
DTSTATUS= 'done              '  /  data transport status                        
SB_HOST = 'kosmosdhs-4m.kpno.noao.edu'  /  iSTB client host                     
SB_ACCOU= 'cache             '  /  iSTB client user account                     
SB_SITE = 'kp                '  /  iSTB host site                               
SB_LOCAL= 'kp                '  /  locale of iSTB daemon                        
SB_DIR1 = '20140921          '  /  level 1 directory in NSA DS                  
SB_DIR2 = 'kp4m              '  /  level 2 directory in NSA DS                  
SB_DIR3 = '2014B-0461        '  /  level 3 directory in NSA DS                  
SB_RECNO=              2025139  /  iSTB sequence number                         
SB_ID   = 'kp2025139         '  /  unique iSTB identifier                       
SB_NAME = 'k4k_140922_013704_fri.fits'  /  name assigned by iSTB                
SB_RTNAM= 'k4k_140922_013704_fri'  /  NSA root name                             
RMCOUNT =                    0  /  remediation counter                          
RECNO   =              2025139  /  NOAO Science Archive sequence number         
CHECKSUM= 'mhElmh9lmhClmh9l'    /  ASCII 1's complement checksum                
DATASUM = '0         '          /  checksum of data records                     
"""    

# SIDE-EFFECTS: fields added to FITS header
# Used istb/src/header.{h,c} for hints.
# raw: nhs_2014_n14_299403.fits
def modify_hdr(hdr, fname):
    missing = missing_in_raw_hdr(hdr)
    if len(missing) > 0:
        raise tex.InsufficientRawHeader(
            'Raw fits file is missing required metadata fields: {}'
            .format(', '.join(sorted(missing)))
            )

    hdr['TADAVERS']    = '0.0.dev1' # NOT REQUIRED, for diagnostics

    # e.g. OBSID = 'kp4m.20141114T122626'
    # e.g. OBSID = 'soar.sam.20141220T015929.7Z'
    #!tele, dt_str = hdr['OBSID'].split('.')

    datestr = None
    tele = None
    if 'COSMOS' == hdr['INSTRUME']:
        tele, dt_str = hdr['OBSID'].split('.')
        datestr, _ = dt_str.split('T')
    elif 'Mosaic1.1' == hdr['INSTRUME']:
        tele, dt_str = hdr['OBSID'].split('.')
        datestr, _ = dt_str.split('T')
    elif 'SOI' == hdr['INSTRUME']:
        tele, inst, dt_str1, dt_str2 = hdr['OBSID'].split('.')
        dt_str = dt_str1 + dt_str2
        datestr, _ = dt_str.split('T')

    # "UTC epoch"
    fmt = '%Y-%m-%dT%H:%M:%S.%f' if 'T' in hdr['DATE-OBS'] else '%Y-%m-%d'
    dateobs = datetime.datetime.strptime(hdr['DATE-OBS'],fmt)

    # Use existing field if it is present, else calc new  one
    hdr['PROPOSER'] = hdr.get('PROPOSER', hdr['PROPID']) #!!!
    hdr['DTACQNAM'] = hdr.get('DTACQNAM', os.path.basename(fname)) 
    hdr['DTINSTRU'] = hdr.get('DTINSTRU', hdr['INSTRUME']) # eg. 'NEWFIRM'
    hdr['DTNSANAM'] = hdr.get('DTNSANAM', os.path.basename(fname))
    hdr['DTPI']     = hdr.get('DTPI',     hdr['PROPOSER'])
    hdr['DTSITE']   = hdr.get('DTSITE',   hdr['OBSERVAT'].lower())
    #! hdr['DTPUBDAT'] = 'NA' # doc says its required, cooked file lacks it
    hdr['DTTELESC'] = hdr.get('DTTELESC', tele)
    hdr['DTTITLE']  = hdr.get('DTTITLE',  'Not derivable from raw metadata!!!')
    # DTUTC cannot be derived exactly from any RAW fields
    # Should be: "post exposure UTC epoch from DTS"
    hdr['DTUTC']    = hdr.get('DTUTC',
                              #slightly wrong!!!
                              dateobs.strftime('%Y-%m-%dT%H:%M:%S')) 

    #! dir1 = datestr
    #! dir2 = tele
    #! dir3 = hdr['PROPID']
    #! hdr['SB_DIR1'] = dir1
    #! hdr['SB_DIR2'] = dir2 
    #! hdr['SB_DIR3'] = dir3
    # e.g. SB_DIR1='20141113', SB_DIR2='kp4m', SB_DIR3='2013B-0236'

    return hdr

# [vagrant@valley ~]$ imeta set -d /tempZone/mountain_mirror/vagrant/13/nhs_2014_n14_299403.fits ftype fits
# [vagrant@valley ~]$ imeta lsw -d /tempZone/mountain_mirror/vagrant/13/nhs_2014_n14_299403.fits
# AVUs defined for dataObj /tempZone/mountain_mirror/vagrant/13/nhs_2014_n14_299403.fits:
# attribute: ftype
# value: fits
# units: 



def add_hdr_fields(fits_file):
    """Add fields to hdr (modify in place) and create filename
 that satisfies http://ast.noao.edu/data/docs.  This new filename is
 just a name.  The corresponding file does not exist.  Its up the the
 caller to rename from old to new if desired.
    """

    hdulist = pyfits.open(fits_file, mode='update') # modify IN PLACE
    hdr = hdulist[0].header # use only first in list. 

    modify_hdr(hdr, fits_file) # Validates raw fits hdr used as input
    
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
    return new_fname, dir1, dir2, dir3

def show_hdr_values(hdr):
    """Show the values for 'interesting' header fields"""
    #!for key in RAW_REQUIRED_FIELDS.union(INGEST_REQUIRED_FIELDS):
    for key in RAW_REQUIRED_FIELDS:
        print('{}="{}"'.format(key,hdr.get(key,'<not given>')),end=', ')
    print()

def fits_compliant(fits_file_list, show_values=False):
    """Check FITS file for complaince with Archive Ingest."""
    bad = 0
    bad_files = []
    for ffile in fits_file_list:
        missing = []
        try:
            #!valid_header(ffile)
            hdr = pyfits.open(ffile)[0].header # use only first in list.
            if show_values:
                show_hdr_values(hdr) # only the "interesting" ones
            modify_hdr(hdr, ffile)
            missing = missing_in_archive_hdr(hdr)
        except Exception as err:
            bad_files.append(ffile)
            bad += 1
            print('{}:\t NOT compliant; {}'.format(ffile, err))
            #!traceback.print_exc()
            continue
        
        if len(missing) == 0:
            print('{}:\t IS compliant'.format(ffile))
        else:
            bad_files.append(ffile)
            bad += 1
            print('{}:\t NOT compliant; Missing fields: {}'
                  .format(ffile, missing))

    #!if (bad > 0):
    #!    print('Non-complaint files: {}'
    #!          .format(', '.join(bad_files)))
    print('\n{} of {} files are NOT compliant (for Archive Ingest)'
          .format(bad, len(fits_file_list)))


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
    parser.add_argument('--values',
                        action='store_true',
                        help='Show header values for interesting fields')
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

    fits_compliant(args.infiles, show_values=args.values)

if __name__ == '__main__':
    main()

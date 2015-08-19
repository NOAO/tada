#! /usr/bin/env python3
"""Fiddling with Fits (tm)

It would be nice if our FITS files always satisified the FITS Standard.
They do not according to:
http://fits.gsfc.nasa.gov/fits_verify.html
(or the standalone version of same)
"""
import sys
import argparse
import logging
import traceback


import astropy.io.fits as pyfits
import os.path
import datetime as dt
import subprocess
 
from . import file_naming as fn
from . import exceptions as tex
from . import hdr_calc_funcs as hf
from . import exceptions as tex

##############################################################################
# "Required" fields per tier per Email from Brian Thomas on 1/7/15
# (Subject:Tiers of complaince and Archive ICD)
#

TIER0_PHDU_RAW_FIELDS = '''OBSTYPE PROCTYPE PRODTYPE DATE-OBS PROPID
   TELESCOP OBSERVAT INSTRUME NAXIS SB_ID SB_RECNO PIPELINE PLVER'''.split()
TIER0_EHDU_RAW_FIELDS = 'NAXIS NAXIS1 NAXIS2 EXTNAME INHERIT'.split()

TIER1_PHDU_RAW_FIELDS = '''OBJECT FILENAME RA DEC EQUINOX RADESYS EXPTIME
   TELRA TELDEC'''.split()
TIER1_EHDU_RAW_FIELDS = 'RA1 DEC1'.split()

TIER1_PHDU_PROCESSED_FIELDS = (TIER1_EHDU_RAW_FIELDS +
                               '''DTTITLE DTACQNAM DTNSANAM DTINSTRU DTTELESC
                               DTSITE DTUTC DTPI DTSITE'''.split())

TIER2_PHDU_RAW_FIELDS = 'AIRMASS HA ZD'.split()
TIER2_EHDU_RAW_FIELDS = 'AIRMASS1'.split()

TIER2_PHDU_PROCESSED_FIELDS = (TIER2_PHDU_RAW_FIELDS +
                               '''CORN1RA CORN2RA CORN3RA CORN4RA CORN1DEC
                               CORN2DEC CORN3DEC CORN4DEC'''.split())
TIER2_EHDU_PROCESSED_FIELDS = (TIER2_EHDU_RAW_FIELDS +
                               '''COR1RA1 COR2RA1 COR3RA1 COR4RA1 COR1DEC1
                               COR2DEC1 COR3DEC1 COR4DEC1'''.split())

TIER3_PHDU_RAW_FIELDS = 'FILTER SEEING'.split()
TIER3_EHDU_RAW_FIELDS = 'SEEING1'.split()



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

#DOC: vvv
# All bets are off in the original FITS file does not contain all of these.
RAW_REQUIRED_FIELDS = set([
    'DATE-OBS',
    'DTSITE',   # Required for standard file name (pg 9, "File Naming Conv...")
    'DTTELESC', # Required for standard file name (pg 9, "File Naming Conv...")
    'DTINSTRU', # Required for standard file name (pg 9, "File Naming Conv...")
    'INSTRUME',
    'OBSERVAT',
    'OBSID',
    # 'PROPID', # Presumably archive uses DTPROPID id instead
    # 'DTPROPID',# could be looked up in schedule so moved to COOKED
    # 'PROPOSER', #!!! will use PROPID when PROPOSER doesn't exist in raw hdr
])

# To be able to ingest a fits file into the archive, all of these must
# be present in the header.
# The commented out lines are Requirements per document, but did not seem to
# be required in Legacy code.
INGEST_REQUIRED_FIELDS = set([
    'SIMPLE',
    'DTPROPID', # observing proposal ID
    'DTCALDAT', # calendar date from observing schedule
    'DTTELESC', # needed to construct full file path in archive
    'DTACQNAM', # file name supplied at telescope; User knows only THIS name
    'DTNSANAM', # file name in archive (renamed from user supplied)
])

# We should try to fill these fields were practical. They are used in
# the archive. Under the portal they may affect ability to query or
# show as the results of queries.  If any of these are missing just
# before ingest, a warning will be logged indicating the missing
# fields.
INGEST_RECOMMENDED_FIELDS = set([
    'DTACQNAM',
    'DTCALDAT', # calendar date from observing schedule
    'DTCOPYRI', # copyright holder of data (ADDED!!!)
    'DTINSTRU',
    'DTNSANAM',
    'DTOBSERV',
    'DTPI',
    'DTPIAFFL',
    'DTPROPID', # observing proposal ID
    'DTSITE',
    'DTTELESC',
    'DTTITLE',
    'OBSERVAT',
    'PROCTYPE',
    'PRODTYPE',
#   'DTACCOUN', # observing account name
#   'DTACQUIS', # host name of data acquisition computer
#   'DTOBSERV', # scheduling institution
#   'DTPIAFFL', # PI affiliation 
#   'DTPUBDAT', # calendar date of public release 
#   'DTUTC',
])    
#DOC: ^^^


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



def print_header(msg, hdr=None, fits_filename=None):
    """Provide HDR or FITS_FILENAME"""
    if hdr == None:
        hdulist = pyfits.open(fits_filename) 
        hdr = hdulist[0].header # use only first in list.
    # Print without blank cards or trailing whitespace
    hdrstr = hdr.tostring(sep='\n',padding=False)
    print('{}: '.format(msg))
    print(*[s.rstrip() for s in hdrstr.splitlines()
            if s.strip() != ''],
          sep='\n')

    
    
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
    missing = required_fields - hdr_keys
    return missing

def missing_in_raw_hdr(hdr):
    """Header from original FITS input to TADA doesn't contain minimum
 acceptable fields."""
    return missing_in_hdr(hdr, RAW_REQUIRED_FIELDS)

def missing_in_archive_hdr(hdr):
    """Header from FITS doesn't contain minimum fields acceptable for
 Archive Ingest."""
    return missing_in_hdr(hdr, INGEST_REQUIRED_FIELDS)

def missing_in_recommended_hdr(hdr):
    "Header from FITS doesn't contain all fields recommended for ingest."
    return missing_in_hdr(hdr, INGEST_RECOMMENDED_FIELDS)

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
            'Missing required metadata keys: {} in file {}'
            .format(missing, hdr.get(DTACQNAM,'NA')))
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
NOCROIPT= 'FullFrame'        / Detector ROI pattern (FullFrame|4kx2k|4kx300|2k
NOCSYS  = 'kpno 4m '           / system ID                                  
NOCNUM  =                    1 / observation number request                 
NOCLAMP = 'off     '           / Dome flat lamp status (on|off|unknown)     
NOCRBIN =                    1 / CCD row binning                            
NOCROICS=                    0 / Detector ROI colum start                   
NOCNPOS =                    1 / observation number in requested number     
NOCROI  = 'disabled'           / Detector ROI flag (enabled|disabled)       
NOCCBIN =                    1 / CCD column binning                         
NOCTYP  = 'FLAT    '         / Observation type (zero|dark|flat|arc|focus|acq|
NOCPOST = 'sky     '         / Calibration position (unknown|init|sky|dfs|lamp
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
KSDPOS  = 'b2k     '         / actual name {between|lo|med|high|narrow|other|o
KSDWPOS =                    6 / wheel actual pos {0|1|2|3|4|5|6}           
KSFILCMD= 'Open    '           / actual name {between|U|B|V|R|I|open}       
KSFW1POS=                    2 / wheel 1 actual pos {0|1|2|3|4|5|6}         
KSFW2POS=                    1 / wheel 2 actual pos {0|1|2|3|4|5|6}         
KSSWPOS =                    2 / wheel actual pos {0|1|2|3|4|5|6}           
KSSPOS  = '4pxB    '         / actual name {between|long|1px|2px|narrow|other|
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
DTTITLE = 'Spectroscopy of Ultra-Low Metallicity Star-Forming Galaxies' / titl
DTCOPYRI= 'AURA              '  /  copyright holder of data                 
DTACQUIS= 'kosmosdhs-4m.kpno.noao.edu' / host name of data acquisition compute
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

def validate_raw_hdr(hdr, orig_fullname):
    missing = missing_in_raw_hdr(hdr)
    if len(missing) > 0:
        raise tex.InsufficientRawHeader(
            'Raw FITS header is missing required metadata fields ({}) '
            'in file {}'
            .format(', '.join(sorted(missing)), orig_fullname))
    return True    

def validate_cooked_hdr(hdr, orig_fullname):
    missing = missing_in_archive_hdr(hdr)
    if len(missing) > 0:
        raise tex.InsufficientArchiveHeader(
            'Modified FITS header is missing required metadata fields ({}) '
            'in file {}'
            .format(', '.join(sorted(missing)), orig_fullname))
    return True

def validate_recommended_hdr(hdr, orig_fullname):
    missing = missing_in_recommended_hdr(hdr)
    if len(missing) > 0:
        logging.warning(
            'Modified FITS header is missing recommended metadata fields ({}) '
            'in file {}'
            .format(', '.join(sorted(missing)), orig_fullname))
    return True

def fits_extension(fname):
    '''Return extension of any file matching <basename>.fits.*, basename.fits
Extension may be: ".fits.fz", ".fits", ".fits.gz", etc'''
    _, ext = os.path.splitext(fname)
    if ext != '.fits':
        _, e2  = os.path.splitext(_)
        ext = e2 + ext
    return ext



# SIDE-EFFECTS: fields added to FITS header
# Used istb/src/header.{h,c} for hints.
# raw: nhs_2014_n14_299403.fits
def modify_hdr(hdr, fname, options, opt_params, forceRecalc=True, **kwargs):
    '''Modify header to suit Archive Ingest. Return fields needed to construct
 new filename that fullfills standards
    options :: e.g. {'INSTRUME': 'KOSMOS', 'OBSERVAT': 'KPNO'}
'''
    orig_fullname = opt_params.get('filename','<no filename option provided>')
    for k,v in options.items():
        if forceRecalc or (k not in hdr):
            hdr[k] = v
    
    # Validate after explicit overrides, before calculated fields.
    # This is because calc-funcs may depend on required fields.
    #!validate_raw_hdr(hdr)

    calc_param = opt_params.get('calchdr',None)
    calc_funcs = []
    if calc_param != None:
        for funcname in calc_param.split(','):
            try:
                func = eval('hf.'+funcname)
                calc_funcs.append(func)
            except:
                traceback.print_exc()
                raise Exception('Function name "{}" given in option "calchdr"'
                                ' does not exist in tada/hdr_calc_funcs.py'
                                .format(funcname))
    logging.debug('calc_funcs={}'.format(calc_funcs))
    chg = dict(hdr.items()) # plain dictionary of hdr; no FITS specific access
    for calcfunc in calc_funcs:
        new = calcfunc(chg, **kwargs)
        chg.update(new)
        logging.debug('new field values={}'.format(new))    
    #! logging.debug('updated field values={}'.format(chg))    
    #! chg, dateobs = fc.calc_hdr(hdr, fname, **options)
    try:
        dateobs = dt.datetime.strptime(chg['DATE-OBS'], '%Y-%m-%dT%H:%M:%S.%f')
    except:
        raise tex.SubmitException(
            'Could parse DATE-OBS field ({}) in header of: {}'
            .format(chg['DATE-OBS'], orig_fullname))

    if forceRecalc:
        for k,v in chg.items():
            hdr[k] = v
    else: # Use existing field if it is present, else use new one
        for k,v in chg.items():
            hdr[k] = hdr.get(k,v)

    # If we have what we need in RAW and doing everything we should in
    # this function, then we should never be missing anything in archive_hdr.
    # This check is therefore here only to catch programming errors.
    #!validate_cooked_hdr(hdr)
    #!validate_recommended_hdr(hdr)
    
    ext = fits_extension(fname)
    return (hdr.get('DTSITE', 'na'),
            hdr.get('DTTELESC', 'na'),
            hdr.get('DTINSTRU', 'na'),
            dateobs, 
            hdr.get('OBSTYPE', 'nota').lower(),
            hdr.get('PROCTYPE', 'nota').lower(),
            hdr.get('PRODTYPE', 'nota').lower(),
            ext[1:])

def show_hdr_values(msg, hdr):
    """Show the values for 'interesting' header fields"""
    #!for key in RAW_REQUIRED_FIELDS.union(INGEST_REQUIRED_FIELDS):
    print('{}: '.format(msg), end='')
    for key in RAW_REQUIRED_FIELDS:
        print('{}="{}"'.format(key,hdr.get(key,'<not given>')),end=', ')
    print()

def get_personality_dict(personality_file):
    cmd = 'source {}; echo $TADAOPTS'.format(personality_file)
    optstr = subprocess.check_output(['bash', '-c', cmd ]).decode()
    options = dict()
    opt_params = dict()
    for opt in optstr.replace('-o ', '').split():
        k, v = opt.split('=')
        if k[0] != '_':
            continue
        if k[1] == '_':
            opt_params[k[2:]] = v
        else:
            options[k[1:]] = v.replace('_', ' ')                
    return options, opt_params
    
def apply_options(options, hdr):
    for k,v in options.items():
        hdr[k] = v  # overwrite with explicit fields from personality

# EXAMPLE:
#   find /data/raw -name "*.fits*" -print0 | xargs --null  fits_compliant
def fits_compliant(fits_file_list,
                   personalities=[],
                   quiet=False,
                   show_values=False, show_header=False, show_stdfname=True,
                   required=False, verbose=False):
    """Check FITS file for complaince with Archive Ingest."""
    if personalities == None:
        personalities = []
    bad = 0
    bad_files = set()
    if required:
        print('These fields MUST be in raw fits header (or provided by '
              'options at submit time). If not, field calculation will not '
              'be attempted, and ingest will be aborted: \n\t{}'
              .format( '\n\t'.join(sorted(RAW_REQUIRED_FIELDS))))

        print('These fields MUST be in hdr given to Ingest. They may '
              'be calculated from raw fits fields and options provided '
              'at submit time. If any of these fields are not in hdr after '
              'calculation, ingest will be aborted: \n\t{}'
              .format( '\n\t'.join(sorted(INGEST_REQUIRED_FIELDS))))

        print('These fields SHOULD be in hdr given to Ingest. They may '
              'be calculated from raw fits fields and options provided '
              'at submit time. If any of these fields are not in hdr after '
              'calculation, portal queries may lack features: \n\t{}'
              .format( '\n\t'.join(sorted(INGEST_RECOMMENDED_FIELDS))))

    
    all_missing_raw = set()
    all_missing_cooked = set()
    all_missing_recommended = set()
    options = dict()
    opt_params = dict()
    for p in personalities:
        opts, prms = get_personality_dict(p)
        options.update(opts)
        opt_params.update(prms)
    #!print('DBG: options={}, opt_params={}'.format(options, opt_params))
    for ffile in fits_file_list:
        valid = True
        missing_raw = []
        missing_cooked = []
        missing_recommended = []
        fname_fields = None
        try:
            #!valid_header(ffile)
            hdr = pyfits.open(ffile)[0].header # use only first in list.
            apply_options(options, hdr)
            missing_raw = missing_in_raw_hdr(hdr)
            fname_fields = modify_hdr(hdr, ffile, options, opt_params)
            missing_cooked = missing_in_archive_hdr(hdr)
            missing_recommended = missing_in_recommended_hdr(hdr)
        except Exception as err:
            if not quiet:
                print('EXCEPTION in fits_compliant: {}'.format(err))
            #!traceback.print_exc()            
            valid = False
        all_missing_raw.update(missing_raw)
        all_missing_cooked.update(missing_cooked)
        all_missing_recommended.update(missing_recommended)
        if (len(missing_raw) + len(missing_cooked)) > 0:
            valid = False

        if show_stdfname and fname_fields != None:
            new_basename = fn.generate_fname(*fname_fields)
            print('{} produced from {}'.format(new_basename, ffile))
        if show_values:
            show_hdr_values('Post modify', hdr) # only "interesting" ones
        if show_header:
            print_header('Post modify', hdr=hdr)

        if valid:
            if not quiet:
                print('{}:\t IS compliant'.format(ffile))
        else:
            bad_files.add(ffile)
            bad += 1
            print('{}:\t NOT compliant; '
                  'Missing fields, raw: {}, cooked: {}, recommended: {}'
                  .format(ffile,
                          sorted(missing_raw),
                          sorted(missing_cooked),
                          sorted(missing_recommended)))

    if (verbose and (bad > 0)):
        print('Non-complaint files: {}'.format(', '.join(bad_files)))

    if len(fits_file_list) > 0:
        if (len(all_missing_raw)
            + len(all_missing_cooked)
            + len(all_missing_recommended)) > 0:
            print('Fields missing from at least one file:\n'
                  '   Raw:         {}\n'
                  '   Cooked:      {}\n'          
                  '   Recommended: {}\n'
                  '   (Cooked & Recommended exclude files that have missing '
                  'Raw fields)'
                  .format(sorted(all_missing_raw),
                          sorted(all_missing_cooked),
                          sorted(all_missing_recommended)))
        print('\n{} of {} files are compliant (for Archive Ingest)'
              .format(len(fits_file_list)-bad, len(fits_file_list)))


##############################################################################

def main():
    "Parse command line arguments and do the work."
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=('Check for compliance of FITS files with respect '
                     'to Archive Ingest'),
        epilog=('EXAMPLES: '
                '\n\t{prog} --required'
                '\n\t{prog} foo.fits bar.fits.fz'
                .format(prog='%(prog)s'))
        )

    parser.add_argument('--version', action='version', version='1.1')
    parser.add_argument('infiles',
                        nargs='*',
                        help='Input file')
    parser.add_argument('-q','--quiet',
                        action='store_true',
                        help='Do not list each compliant file')
    parser.add_argument('-p','--personality',
                        action='append',
                        help=('Personality file that adds explicit and '
                        'calculated fields to each FITS hdr'))
    parser.add_argument('--required',
                        action='store_true',
                        help='Report on fields required for Archive Ingest')
    parser.add_argument('--values',
                        action='store_true',
                        help='Show header values for interesting fields')
    parser.add_argument('--header',
                        action='store_true',
                        help='Show full header')
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

    fits_compliant(args.infiles,
                   personalities=args.personality,
                   quiet=args.quiet,
                   required=args.required,
                   show_values=args.values,
                   show_header=args.header)

if __name__ == '__main__':

    main()

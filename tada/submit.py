#! /usr/bin/env python
"""<<Python script callable from command line.  Put description here.>>
"""
# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging

# From: http://ast.noao.edu/data/docs
table1_str = '''
| Site         | Telescope | Instrument | Type                   | Prefix |
|--------------+-----------+------------+------------------------+--------|
| Cerro Pachon | SOAR      | Goodman    | spectograph            | psg    |
| Cerro Pachon | SOAR      | OSIRIS     | IR imager/spectrograph | pso    |
| Cerro Pachon | SOAR      | SOI        | image                  | psi    |
| Cerro Pachon | SOAR      | Spartan    | IR imager              | pss    |
| Cerro Pachon | SOAR      | SAM        | imager                 | psa    |
| Cerro Tololo | Blanco 4m | DECam      | imager                 | c4d    |
| Cerro Tololo | Blanco 4m | COSMOS     | spectrograph           | c4c    |
| Cerro Tololo | Blanco 4m | ISPI       | IR imager              | c4i    |
| Cerro Tololo | Blanco 4m | Arcon      | imagers/spectrographs  | c4a    |
| Cerro Tololo | Blanco 4m | Mosaic     | imager                 | c4m    |
| Cerro Tololo | Blanco 4m | NEWFIRM    | IR imager              | c4n    |
| Cerro Tololo | 1.5m      | Chiron     | spectrograph           | c15e   |
| Cerro Tololo | 1.5m      | Arcon      | spectrograph           | c15s   |
| Cerro Tololo | 1.3m      | ANDICAM    | O/IR imager            | c13a   |
| Cerro Tololo | 1.0m      | Y4KCam     | imager                 | c1i    |
| Cerro Tololo | 0.9m      | Arcon      | imager                 | c09i   |
| Cerro Tololo | lab       | COSMOS     | spectrograph           | clc    |
| Kitt Peak    | Mayall 4m | Mosaic     | imager                 | k4m    |
| Kitt Peak    | Mayall 4m | NEWFIRM    | IR imager              | k4n    |
| Kitt Peak    | Mayall 4m | KOSMOS     | spectograph            | k4k    |
| Kitt Peak    | Mayall 4m | ICE        | Opt. imagers/spectro.  | k4i    |
| Kitt Peak    | Mayall 4m | Wildfire   | IR imager/spectro.     | k4w    |
| Kitt Peak    | Mayall 4m | Flamingos  | IR imager/spectro.     | k4f    |
| Kitt Peak    | Mayall 4m | WHIRC      | IR imager              | kww    |
| Kitt Peak    | Mayall 4m | Bench      | spectrograph           | kwb    |
| Kitt Peak    | Mayall 4m | MiniMo/ICE | imager                 | kwi    |
| Kitt Peak    | Mayall 4m | (p)ODI     | imager                 | kwo    |
| Kitt Peak    | Mayall 4m | MOP/ICE    | imager/spectrograph    | k21i   |
| Kitt Peak    | Mayall 4m | Wildfire   | IR imager/spectrograph | k21w   |
| Kitt Peak    | Mayall 4m | Falmingos  | IR imager/spectrograph | k21f   |
| Kitt Peak    | Mayall 4m | GTCam      | imager                 | k21g   |
| Kitt Peak    | Mayall 4m | MOP/ICE    | spectrograph           | kcfs   |
| Kitt Peak    | Mayall 4m | HDI        | imager                 | k09h   |
| Kitt Peak    | Mayall 4m | Mosaic     | imager                 | k09m   |
| Kitt Peak    | Mayall 4m | ICE        | imager                 | k09i   |
'''


obsLUT = {
    #Observation-type:             code  
    'object':                     'o',  
    'Photometric standard      ': 'p',
    'Bias                      ': 'z',
    'Dome or projector flat    ': 'f',
    'sky':                        's',
    'Dark                      ': 'd',
    'Calibration or comparison ': 'c',
    'Illumination calibration  ': 'i',
    'Focus                     ': 'g',
    'Fringe                    ': 'h',
    'Pupil                     ': 'r',
    'NOTA                      ': 'u',
}

procLUT = {
    #Processing-type: code   
    'Raw      ': 'r',
    'InstCal  ': 'o',
    'MasterCal': 'c',
    'Projected': 'p',
    'Stacked  ': 's',
    'SkySub   ': 'k',
    'NOTA': 'u',
}

prodLUT = {
    #Product-type:         code    
    'Image               ': 'i ',   
    'Image 2nd version 1 ': 'j ',   
    'Dqmask              ': 'd ',   
    'Expmap              ': 'e ',   
    'Graphics (size)     ': 'gN',   
    'Weight              ': 'w ',   
    'NOTA':                 'u ',   
]


def valid_header(fits_file):
    "Read FITS metadata and insure it has what we need. Return (success, message)."
    requiredFitsFields = set([
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
    try:
        # Only look at first/primary HDU?!!! (Header Data Unit)
        hdu = pyfits.open(fits_file)[0] # can be compressed
        hdr_keys = set(hdu.header.keys())
    except Exception as err:
        return False, 'Metadata keys could not be read: %s' % err

    missing = sorted(requiredFitsFields - hdr_keys)
    if len(missing) > 0:
        return (False,
                'FITS file is missing required metadata keys: %s'
                % (missing,))
    return True, None


# Used istb/src/header.{h,c} for hints.
def molest_header(fits_file):
    """Add fields to hdr and create filename that 
    satisfies http://ast.noao.edu/data/docs"""
    
    hdr = pyfits.open(fils_file)[0].header
    hdr['SB_DIR1'] = hdr['NOCUTC'] # or derive from DATE-OBS, OBSID?
    hdr['SB_DIR2'] = hdr['OBSID'].split('.')[0]
    hdr['SB_DIR3'] = hdr['PROPID'] 

    hdr['DTACQNAM'] = '' # file name supplied at telescope
    hdr['DTINSTRU'] = hdr['INSTRUME']
    #hdr['DTNSANAM'] = '' #file name in NOAO Science Archive            
    hdr['DTPI']     = hdr['PROPOSER']
    hdr['DTSITE']   = hdr['']
    hdr['DTTELESC'] = hdr['OBSID'].split('.')[0]
    hdr['DTTITLE']  = hdr['']
    hdr['DTUTC']    = hdr['']


    # e.g. "k4k_140923_024819_uri.fits.fz"
    (date,time) = hdr['OBSID'].split('.')[1].split('T')
    fields = dict(
        instrument=hdr['DTINSTRU'],
        date=date,
        time=time,
        obstype=obsLUT[hdr.get('OBSTYPE','NOTA')],
        proctype=procLUT[hdr.get('PROCTYPE','NOTA')],
        prodtype=prodLUT[hdr.get('PRODTYPE','NOTA')],
        )
    new_fname = "{instrument}_{date}_{time}_{obstype}{proctype}{prodtype}.{ext}".format(**fields)
    
    
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
    
    return new_fits_file


    
def submit(fits_file):
    "Ingest a FITS file into archive, or stash it in Mitigation queue"
    validate_header(fits_file)
    new_name = molest_header()
    stuff_in_irods()
    ingest()



##############################################################################

def main():
    "Parse command line arguments and do the work."
    print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
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

    submit(args.infile)

if __name__ == '__main__':
    main()

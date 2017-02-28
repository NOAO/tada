"Create filename that satisfies standard naming convention."

import logging
import os.path
import datetime as dt
from pathlib import PurePath 
import csv

from . import exceptions as tex
from . import settings

#! From: http://ast.noao.edu/data/docs
#!table1_str = '''
#!| Site         | Telescope | Instrument | Type                   | Prefix |
#!|--------------+-----------+------------+------------------------+--------|
#!| Cerro Pachon | SOAR      | Goodman    | spectograph            | psg    |
#!| Cerro Pachon | SOAR      | OSIRIS     | IR imager/spectrograph | pso    |
#!| Cerro Pachon | SOAR      | SOI        | image                  | psi    |
#!| Cerro Pachon | SOAR      | Spartan    | IR imager              | pss    |
#!| Cerro Pachon | SOAR      | SAM        | imager                 | psa    |
#!| Cerro Tololo | Blanco 4m | DECam      | imager                 | c4d    |
#!| Cerro Tololo | Blanco 4m | COSMOS     | spectrograph           | c4c    |
#!| Cerro Tololo | Blanco 4m | ISPI       | IR imager              | c4i    |
#!| Cerro Tololo | Blanco 4m | Arcon      | imagers/spectrographs  | c4a    |
#!| Cerro Tololo | Blanco 4m | Mosaic     | imager                 | c4m    |
#!| Cerro Tololo | Blanco 4m | NEWFIRM    | IR imager              | c4n    |
#!| Cerro Tololo | 1.5m      | Chiron     | spectrograph           | c15e   |
#!| Cerro Tololo | 1.5m      | Arcon      | spectrograph           | c15s   |
#!| Cerro Tololo | 1.3m      | ANDICAM    | O/IR imager            | c13a   |
#!| Cerro Tololo | 1.0m      | Y4KCam     | imager                 | c1i    |
#!| Cerro Tololo | 0.9m      | Arcon      | imager                 | c09i   |
#!| Cerro Tololo | lab       | COSMOS     | spectrograph           | clc    |
#!| Kitt Peak    | Mayall 4m | Mosaic     | imager                 | k4m    |
#!| Kitt Peak    | Mayall 4m | NEWFIRM    | IR imager              | k4n    |
#!| Kitt Peak    | Mayall 4m | KOSMOS     | spectograph            | k4k    |
#!| Kitt Peak    | Mayall 4m | ICE        | Opt. imagers/spectro.  | k4i    |
#!| Kitt Peak    | Mayall 4m | Wildfire   | IR imager/spectro.     | k4w    |
#!| Kitt Peak    | Mayall 4m | Flamingos  | IR imager/spectro.     | k4f    |
#!| Kitt Peak    | Mayall 4m | WHIRC      | IR imager              | kww    |
#!| Kitt Peak    | Mayall 4m | Bench      | spectrograph           | kwb    |
#!| Kitt Peak    | Mayall 4m | MiniMo/ICE | imager                 | kwi    |
#!| Kitt Peak    | Mayall 4m | (p)ODI     | imager                 | kwo    |
#!| Kitt Peak    | Mayall 4m | MOP/ICE    | imager/spectrograph    | k21i   |
#!| Kitt Peak    | Mayall 4m | Wildfire   | IR imager/spectrograph | k21w   |
#!| Kitt Peak    | Mayall 4m | Falmingos  | IR imager/spectrograph | k21f   |
#!| Kitt Peak    | Mayall 4m | GTCam      | imager                 | k21g   |
#!| Kitt Peak    | Mayall 4m | MOP/ICE    | spectrograph           | kcfs   |
#!| Kitt Peak    | Mayall 4m | HDI        | imager                 | k09h   |
#!| Kitt Peak    | Mayall 4m | Mosaic     | imager                 | k09m   |
#!| Kitt Peak    | Mayall 4m | ICE        | imager                 | k09i   |
#!'''


# MOVED to external file, read in settings.py
#!# CONTAINS DUPLICATES!!! (e.g. "Arcon") needs Telescope for disambiguation.
#!stiLUT = {
#!    # (site, telescope,instrument): Prefix 
#!    ('cp', 'soar', 'goodman'):   'psg',  
#!    ('cp', 'soar', 'goodman spectrograph'):   'psg',  # added
#!    ('cp', 'soar', 'osiris'):    'pso',  
#!    ('cp', 'soar', 'soi'):       'psi',  
#!    ('cp', 'soar', 'spartan'):   'pss',  
#!    ('cp', 'soar', 'spartan ir camera'):   'pss',   # added
#!    ('cp', 'soar', 'sami'):      'psa',  
#!    ('ct', 'ct4m', 'decam'):     'c4d',  
#!    ('ct', 'ct4m', 'cosmos'):    'c4c', 
#!    ('ct', 'ct4m', 'ispi'):      'c4i',  
#!   #('ct', 'ct4m', 'arcon'):     'c4a',   # removed <2016-03-17 Thu>
#!    ('ct', 'ct4m', 'mosaic'):    'c4m',  
#!    ('ct', 'ct4m', 'newfirm'):   'c4n',  
#!   #('ct', 'ct4m', 'triplespec'):'c4t', 
#!    ('ct', 'ct4m', 'arcoiris'):  'c4ai',  # added <2016-03-17 Thu>
#!    ('ct', 'ct15m', 'chiron'):   'c15e',  
#!    ('ct', 'ct15m', 'echelle'):  'c15e',  # added
#!    ('ct', 'ct15m', 'arcon'):    'c15s',  
#!    ('ct', 'ct13m', 'andicam'):  'c13a',  
#!    ('ct', 'ct1m', 'y4kcam'):    'c1i',  
#!    #('ct', 'ct09m', 'arcon'):    'c09i',  
#!    ('ct', 'ct09m', 'ccd_imager'): 'c09i', # renamed from arcon
#!    ('ct', 'ctlab', 'cosmos'):   'clc',  
#!    ('kp', 'kp4m', 'mosaic'):    'k4m',  
#!    ('kp', 'kp4m', 'mosaic3'):   'k4m',  # added
#!    ('kp', 'kp4m', 'newfirm'):   'k4n',  
#!    ('kp', 'kp4m', 'kosmos'):    'k4k',  
#!    ('kp', 'kp4m', 'cosmos'):    'k4k',  
#!    ('kp', 'kp4m', 'ice'):       'k4i',  
#!    ('kp', 'kp4m', 'wildfire'):  'k4w',  
#!    ('kp', 'kp4m', 'flamingos'): 'k4f',  
#!    ('kp', 'kp35m', 'whirc'):    'kww',  
#!    ('kp', 'wiyn', 'whirc'):     'kww',  # added
#!    ('kp', 'wiyn', 'bench'):     'kwb',  # changed tele (kp35m) <2016-06-17 Fri>
#!    ('kp', 'kp35m', 'minimo/ice'):'kwi',  
#!    ('kp', 'kp35m', '(p)odi'):    'kwo',  
#!    ('kp', 'kp21m', 'mop/ice'):   'k21i',  
#!    ('kp', 'kp21m', 'wildfire'):  'k21w',  
#!    ('kp', 'kp21m', 'falmingos'): 'k21f',  
#!    ('kp', 'kp21m', 'gtcam'):     'k21g',  
#!    ('kp', 'kpcf', 'mop/ice'):   'kcfs',  
#!    ('kp', 'kp09m', 'hdi'):       'k09h',  
#!    ('kp', 'kp09m', 'mosaic'):    'k09m',  
#!    ('kp', 'kp09m', 'ice'):       'k09i',
#!    ('kp', 'bok23m','90prime'):   'ksb',  # BOK
#!    ('ct', 'bok23m','kosmos'):   'ksb',  # fake, for testing
#!    #'NOTA':      'uuuu',  
#!}
#!
#!obsLUT = {
#!    #Observation-type:           code  
#!    'object':                    'o',  
#!    'photometric standard':      'p',
#!    'bias':                      'z',
#!    'zero':                      'z', # added 5/8/15 for bok
#!    'dome or projector flat':    'f',
#!    'dome flat':                 'f', # added 1/8/16 for mosaic3
#!    'dflat':                     'f', # added 10/23/15 (per dsid.c)
#!    'flat':                      'f',
#!    'projector':                 'f', # added 10/23/15 (per dsid.c)
#!    'sky':                       's',
#!    'skyflat':                   's', # added 10/23/15 (per dsid.c)
#!    'dark':                      'd',
#!    'calibration':               'c', # added 2/1/16 for ct15m-echelle
#!    'calibration or comparison': 'c',
#!    'comp':                      'c', # added 10/23/15 (per dsid.c)
#!    'comparison':                'c', # added 10/23/15 (per dsid.c)
#!    'illumination calibration':  'i',
#!    'focus':                     'g',
#!    'fringe':                    'h',
#!    'pupil':                     'r',
#!    'nota':                      'u',
#!}
#!
#!procLUT = {
#!    #Processing-type: code   
#!    'raw': 'r',
#!    'instcal': 'o',
#!    'mastercal': 'c',
#!    'projected': 'p',
#!    'stacked': 's',
#!    'skysub': 'k',
#!    'nota': 'u',
#!}
#!
#!prodLUT = {
#!    #Product-type:         code    
#!    'image':               'i',   
#!    'image 2nd version 1': 'j',   
#!    'dqmask':              'd',   
#!    'expmap':              'e',   
#!    'graphics (size)':     'gn',   
#!    'weight':              'w',   
#!    'nota':                'u',
#!    'wtmap':               '-',  # Found in pipeline, not used for name
#!    'resampled':           '-',  # Found in pipeline, not used for name
#!    }

def fits_extension(fname):
    '''Return extension of any file matching <basename>.fits.*, basename.fits
Extension may be: ".fits.fz", ".fits", ".fits.gz", etc'''
    _, ext = os.path.splitext(fname)
    if ext != '.fits':
        _, e2  = os.path.splitext(_)
        ext = e2 + ext
    return ext[1:]

def get_hdr_fname(fitsname):
    """Derive HDR filename from FITS filename. 
    Handle files like: x.fits, x.fits.fz, x.fits.gz"""
    extension = ''
    ext_list = PurePath(fitsname).suffixes
    for ext in reversed(ext_list):
        extension = ext + extension
        if ext == '.fits':
            break
    return(fitsname.replace(extension, '.hdr'))


def generate_fname(hdr, # dict
                   ext,
                   orig=None,
                   require_known=True,
                   sti_fname='/etc/tada/prefix_table.csv',
                   tag=None ):
    """Generate standard filename from metadata values.
e.g. k4k_140923_024819_uri.fits.fz"""
    site = hdr.get('DTSITE','nota').lower()
    telescope = hdr.get('DTTELESC','nota').lower()
    instrument = hdr.get('DTINSTRU','nota').lower()
    obstype = hdr.get('OBSTYPE', 'nota').lower()
    proctype = hdr.get('PROCTYPE', 'nota').lower()
    prodtype = hdr.get('PRODTYPE', 'nota').lower()
    serno = hdr.get('DTSERNO')
    logging.debug('generate_fname: site="{}", tele="{}", instrument="{}", '
                  'obstype="{}", proctype="{}", prodtype="{}"'
                  .format(site, telescope, instrument,
                          obstype, proctype, prodtype))

    #!if os.path.exists(sti_fname):
    #!    lut=dict()
    #!    with open(sti_fname) as csvfile:
    #!        for s, t,i,pfx,*rest in csv.reader(csvfile):
    #!            if site[0] == '#': continue
    #!            lut[(s, t,i)] = pfx
    #!stiLUT.update(lut)
    
    # Do NOT allow any "u" parts to the generated filename
    if require_known:
        if (site, telescope, instrument) not in settings.stiLUT:
            msg=('Unknown combination for stiLUT: SITE({}), TELESCOPE({}), '
                 'and INSTRUMENT({}) (in {})'
                 .format(site, telescope, instrument,  orig))
            raise tex.NotInLut(msg)
        if proctype not in settings.procLUT:
            raise tex.NotInLut('Unknown PROCTYPE({}) in procLUT({}) (for {})'
                               .format(proctype,
                                       sorted(settings.procLUT.keys()),  orig))
        if prodtype not in settings.prodLUT:
            raise tex.NotInLut('Unknown PRODTYPE({}) in prodLUT({}) (for {})'
                               .format(prodtype,
                                       sorted(settings.prodLUT.keys()), orig))

    if obstype not in settings.obsLUT:
        logging.warning('Unknown OBSTYPE({}) in obsLUT({}) (for {})'
                        .format(obstype, sorted(settings.obsLUT.keys()), orig))
 
    # e.g. DATEOBS='2002-12-25T00:00:00.000001'
    obsdt = dt.datetime.strptime(hdr.get('DATE-OBS','NA'),
                                 '%Y-%m-%dT%H:%M:%S.%f')
    date = obsdt.date().strftime('%y%m%d')
    time = obsdt.time().strftime('%H%M%S')

    fields = dict(
        prefix=settings.stiLUT.get((site, telescope, instrument), 'uuuu'),
        date=date,
        time=time,
        obstype=settings.obsLUT.get(obstype, 'u'),  # if not in LUT, use "u"!!!
        proctype=settings.procLUT.get(proctype,'u'),
        prodtype=settings.prodLUT.get(prodtype,'u'),
        serno=serno,
        tag=tag,
        ext=ext,
        )

    #!std='{prefix}_{date}_{time}_{obstype}{proctype}{prodtype}'
    #!if tag != None:
    #!    fields['tag'] = tag
    #!    new_fname = (std+"_{tag}.{ext}").format(**fields)
    #!else:
    #!    new_fname = (std+".{ext}").format(**fields)

    # Add "Flavor field"
    std='{prefix}_{date}_{time}_{obstype}{proctype}{prodtype}'
    if serno != None:
        std += '_s{serno}'
    if (tag != None) and (tag != ''):
        std += '_t{tag}'
    std += '.{ext}'

    return std.format(**fields)


# /Volumes/archive/mtn/20150518/kp4m/2015A-0253/k4k_150519_111338_ori.hdr
# /Volumes/archive/mtn/20150518/kp4m/2015A-0253/k4k_150519_111338_ori.fits.fz  
#
# /Volumes/archive/pipeline/Q20150518/DEC14A/20140310/c4d_140311_013647_opi_g_v2.hdr
# /Volumes/archive/pipeline/Q20150518/DEC14A/20140310/c4d_140311_013647_opi_g_v2.fits.fz
def generate_archive_path(hdr, source='raw'):
    '''Generate filename irods path sufficient for Portal staged FTP
functioning. All modifications to hdr should be done before calling
this function.'''
    #logging.debug('DBG: generate_archive_path({},source={}'.format(hdr,source))
    if source == 'raw':
        return PurePath('/noao-tuc-z1/mtn',
                        hdr['DTCALDAT'].replace('-',''),
                        hdr['DTTELESC'],
                        hdr['DTPROPID'])
    elif source == 'dome':
        return PurePath('/noao-tuc-z1/mtn',
                        hdr['DTCALDAT'].replace('-',''),
                        hdr['DTTELESC'],
                        hdr['DTPROPID'])
    elif source == 'pipeline':
        return PurePath('/noao-tuc-z1/pipe',
                        hdr['DTCALDAT'].replace('-',''),
                        hdr['DTTELESC'],
                        hdr['DTPROPID'])
    else:
        raise Exception('Unrecognized source type: "{}"'.format(source))
    # END

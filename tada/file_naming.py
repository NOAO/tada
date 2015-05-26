"Create filename that satisfies standard naming convention."

import logging
import os.path
import datetime as dt
from pathlib import PurePath 

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


# CONTAINS DUPLICATES!!! (e.g. "Arcon") needs Telescope for disambiguation.
stiLUT = {
    # (site, telescope,instrument): Prefix 
    ('cp', 'soar', 'goodman'):   'psg',  
    ('cp', 'soar', 'osiris'):    'pso',  
    ('cp', 'soar', 'soi'):       'psi',  
    ('cp', 'soar', 'spartan'):   'pss',  
    ('cp', 'soar', 'sam'):       'psa',  
    ('ct', 'ct4m', 'decam'):     'c4d',  
    ('ct', 'ct4m', 'cosmos'):    'c4c',  
    ('ct', 'ct4m', 'ispi'):      'c4i',  
    ('ct', 'ct4m', 'arcon'):     'c4a',  
    ('ct', 'ct4m', 'mosaic'):    'c4m',  
    ('ct', 'ct4m', 'newfirm'):   'c4n',  
    ('ct', 'ct15m', 'chiron'):   'c15e',  
    ('ct', 'ct15m', 'arcon'):    'c15s',  
    ('ct', 'ct13m', 'andicam'):  'c13a',  
    ('ct', 'ct1m', 'y4kcam'):    'c1i',  
    ('ct', 'ct09m', 'arcon'):    'c09i',  
    ('ct', 'ctlab', 'cosmos'):   'clc',  
    ('kp', 'kp4m', 'mosaic'):    'k4m',  
    ('kp', 'kp4m', 'newfirm'):   'k4n',  
    ('kp', 'kp4m', 'kosmos'):    'k4k',  
    ('kp', 'kp4m', 'ice'):       'k4i',  
    ('kp', 'kp4m', 'wildfire'):  'k4w',  
    ('kp', 'kp4m', 'flamingos'): 'k4f',  
    ('kp', 'kp35m', 'whirc'):     'kww',  
    ('kp', 'kp35m', 'bench'):     'kwb',  
    ('kp', 'kp35m', 'minimo/ice'):'kwi',  
    ('kp', 'kp35m', '(p)odi'):    'kwo',  
    ('kp', 'kp21m', 'mop/ice'):   'k21i',  
    ('kp', 'kp21m', 'wildfire'):  'k21w',  
    ('kp', 'kp21m', 'falmingos'): 'k21f',  
    ('kp', 'kp21m', 'gtcam'):     'k21g',  
    ('kp', 'kpcf', 'mop/ice'):   'kcfs',  
    ('kp', 'kp09m', 'hdi'):       'k09h',  
    ('kp', 'kp09m', 'mosaic'):    'k09m',  
    ('kp', 'kp09m', 'ice'):       'k09i',
    ('kp', 'bok23m','90prime'):   'ksb',  # BOK
    #'NOTA':      'uuuu',  
}

obsLUT = {
    #Observation-type:           code  
    'object':                    'o',  
    'photometric standard':      'p',
    'bias':                      'z',
    'zero':                      'z',  # added 5/8/15 for bok
    'dome or projector flat':    'f',
    'flat':                      'f',
    'sky':                       's',
    'dark':                      'd',
    'calibration or comparison': 'c',
    'illumination calibration':  'i',
    'focus':                     'g',
    'fringe':                    'h',
    'pupil':                     'r',
    'nota':                      'u',
}

procLUT = {
    #Processing-type: code   
    'raw': 'r',
    'instcal': 'o',
    'mastercal': 'c',
    'projected': 'p',
    'stacked': 's',
    'skysub': 'k',
    'nota': 'u',
}

prodLUT = {
    #Product-type:         code    
    'image': 'i',   
    'image 2nd version 1': 'j',   
    'dqmask': 'd',   
    'expmap': 'e',   
    'graphics (size)': 'gn',   
    'weight': 'w',   
    'nota':                 'u',   
    }


def generate_fname(site, telescope, instrument,
                   obsdt, obstype, proctype, prodtype, ext,
                   orig=None,
                   jobid=False,
                   wunk=False):
    """Generate standard filename from metadata values.
e.g. k4k_140923_024819_uri.fits.fz"""
    if wunk != False:
        if 'u' == obsLUT.get(obstype, 'u'):
            logging.warning('Unknown OBSTYPE "{}" in {}'
                            .format(obstype, orig))
        if 'u' == procLUT.get(proctype, 'u'):
            logging.warning('Unknown PROCTYPE "{}" in {}'
                            .format(proctype, orig))
        if 'u' == prodLUT.get(prodtype, 'u'):
            logging.warning('Unknown PRODTYPE "{}" in {}'
                            .format(prodtype, orig))

 
    #!(date,time) = datetime.split('.')[-1].split('T')
    # e.g. "20141220T015929"
    date = obsdt.date().strftime('%y%m%d')
    time = obsdt.time().strftime('%H%M%S')

    fields = dict(
        instrument=stiLUT.get((site.lower(),
                               telescope.lower(),
                               instrument.lower()),
                              'uuuu'),
        date=date,
        time=time,
        obstype=obsLUT.get(obstype, 'u'),    # if not in LUT, use "u"!!!
        proctype=procLUT.get(proctype, 'u'), # if not in LUT, use "u"!!!
        prodtype=prodLUT.get(prodtype, 'u'), # if not in LUT, use "u"!!!
        ext=ext,
        )

    std='{instrument}_{date}_{time}_{obstype}{proctype}{prodtype}'
    if jobid:
        fields['jobid'] = jobid
        new_fname = (std+"_{jobid}.{ext}").format(**fields)
    else:
        new_fname = (std+".{ext}").format(**fields)
    return new_fname

# UNDER CONSTRUCTION
def generate_archive_basename(hdr, origfname, jobid=False, wunk=False):
    '''Generate standard filename from metadata values. All modifications
to hdr should be done before calling this function.  Returns something
like: k4k_140923_024819_uri.fits.fz'''
    obsdt = dt.datetime.strptime(hdr['DATE-OBS'], '%Y-%m-%dT%H:%M:%S.%f')
    date = obsdt.date().strftime('%y%m%d')
    time = obsdt.time().strftime('%H%M%S')
    _,ext = os.path.splitext(origfname)
    fields = dict(
        instrument = hdr.get('INSTRUME'),
        date = date,
        time=time,
        obstype = hdr.get('OBSTYPE'),
        proctype = hdr.get('PROCTYPE'),
        prodtype = hdr.get('PRODTYPE'),
        extension = ext[1:]
        )
    std='{instrument}_{date}_{time}_{obstype}{proctype}{prodtype}'
    if jobid:
        fields['jobid'] = jobid
        new_fname = (std+"_{jobid}.{extension}").format(**fields)
    else:
        new_fname = (std+".{extension}").format(**fields)
    return new_fname



# /Volumes/archive/mtn/20150518/kp4m/2015A-0253/k4k_150519_111338_ori.hdr
# /Volumes/archive/mtn/20150518/kp4m/2015A-0253/k4k_150519_111338_ori.fits.fz  
#
# /Volumes/archive/pipeline/Q20150518/DEC14A/20140310/c4d_140311_013647_opi_g_v2.hdr
# /Volumes/archive/pipeline/Q20150518/DEC14A/20140310/c4d_140311_013647_opi_g_v2.fits.fz
def generate_archive_path(hdr, source='raw'):
    '''Generate filename irods path sufficient for Portal staged FTP
functioning. All modifications to hdr should be done before calling
this function.'''
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
        return PurePath('/noao-tuc-z1/pipeline',
                        'Q_unknownday',
                        'unknown',
                        hdr['DTCALDAT'].replace('-',''))
    else:
        raise Exception('Unrecognized source type: "{}"'.format(source))
    return None

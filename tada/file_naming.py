"Create filename that satisfies standard naming convention."

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


# CONTAINS DUPLICATES!!! (e.g. "Arcon") needs Telescope for disambiguation.
instrumentLUT = {
    # Instrument, Prefix 
    'goodman':   'psg',  
    'osiris':    'pso',  
    'soi':       'psi',  
    'spartan':   'pss',  
    'sam':       'psa',  
    'decam':     'c4d',  
    'cosmos':    'c4c',  
    'ispi':      'c4i',  
    'arcon':     'c4a',  
    'mosaic':    'c4m',  
    'newfirm':   'c4n',  
    'chiron':    'c15e',  
    'arcon':     'c15s',  
    'andicam':   'c13a',  
    'y4kcam':    'c1i',  
    'arcon':     'c09i',  
    'cosmos':    'clc',  
    'mosaic':    'k4m',  
    'newfirm':   'k4n',  
    'kosmos':    'k4k',  
    'ice':       'k4i',  
    'wildfire':  'k4w',  
    'flamingos': 'k4f',  
    'whirc':     'kww',  
    'bench':     'kwb',  
    'minimo/ice':'kwi',  
    '(p)odi':    'kwo',  
    'mop/ice':   'k21i',  
    'wildfire':  'k21w',  
    'falmingos': 'k21f',  
    'gtcam':     'k21g',  
    'mop/ice':   'kcfs',  
    'hdi':       'k09h',  
    'mosaic':    'k09m',  
    'ice':       'k09i',
    #
    '90prime':   'kb23',  # BOK
    #
    'NOTA':      'uuuu',  
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


def generate_fname(instrument, obsdt, obstype, proctype, prodtype, ext,
                   orig=None,
                   jobid=False,
                   wunk=False):
    """Generate standard filename from metadata values.
e.g. k4k_140923_024819_uri.fits.fz"""
    logging.debug('generate_fname({},{},{},{},{},{})'
                  .format(instrument, obsdt, obstype, proctype, prodtype, ext))
    logging.debug('generate_fname(jobid={}, wunk={})'
                  .format(jobid, wunk))
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
        instrument=instrumentLUT.get(instrument.lower(),'uuuu'),
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

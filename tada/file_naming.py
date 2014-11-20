"Create filename that satisfies standard naming convention."

import pyfits

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
    'Goodman':   'psg',  
    'OSIRIS':    'pso',  
    'SOI':       'psi',  
    'Spartan':   'pss',  
    'SAM':       'psa',  
    'DECam':     'c4d',  
    'COSMOS':    'c4c',  
    'ISPI':      'c4i',  
    'Arcon':     'c4a',  
    'Mosaic':    'c4m',  
    'NEWFIRM':   'c4n',  
    'Chiron':    'c15e',  
    'Arcon':     'c15s',  
    'ANDICAM':   'c13a',  
    'Y4KCam':    'c1i',  
    'Arcon':     'c09i',  
    'COSMOS':    'clc',  
    'Mosaic':    'k4m',  
    'NEWFIRM':   'k4n',  
    'KOSMOS':    'k4k',  
    'ICE':       'k4i',  
    'Wildfire':  'k4w',  
    'Flamingos': 'k4f',  
    'WHIRC':     'kww',  
    'Bench':     'kwb',  
    'MiniMo/ICE':'kwi',  
    '(p)ODI':    'kwo',  
    'MOP/ICE':   'k21i',  
    'Wildfire':  'k21w',  
    'Falmingos': 'k21f',  
    'GTCam':     'k21g',  
    'MOP/ICE':   'kcfs',  
    'HDI':       'k09h',  
    'Mosaic':    'k09m',  
    'ICE':       'k09i',
    #
    'NOTA':      'uuuu',  
}

obsLUT = {
    #Observation-type:           code  
    'object':                    'o',  
    'Photometric standard':      'p',
    'Bias':                      'z',
    'Dome or projector flat':    'f',
    'sky':                       's',
    'Dark':                      'd',
    'Calibration or comparison': 'c',
    'Illumination calibration':  'i',
    'Focus':                     'g',
    'Fringe':                    'h',
    'Pupil':                     'r',
    'NOTA':                      'u',
}

procLUT = {
    #Processing-type: code   
    'Raw': 'r',
    'InstCal': 'o',
    'MasterCal': 'c',
    'Projected': 'p',
    'Stacked': 's',
    'SkySub': 'k',
    'NOTA': 'u',
}

prodLUT = {
    #Product-type:         code    
    'Image': 'i',   
    'Image 2nd version 1': 'j',   
    'Dqmask': 'd',   
    'Expmap': 'e',   
    'Graphics (size)': 'gN',   
    'Weight': 'w',   
    'NOTA':                 'u',   
    }


def generate_fname(instrument, datetime, obstype, proctype, prodtype):
    """Generate standard filename from metadata values.
e.g. k4k_140923_024819_uri.fits.fz"""


    (date,time) = datetime.split('.')[1].split('T')

    fields = dict(
        instrument=instrumentLUT[instrument],
        date=date,
        time=time,
        obstype=obsLUT[obstype],    
        proctype=procLUT.get(proctype, 'u'), # if not in LUT, use "u"!!!
        prodtype=prodLUT.get(prodtype, 'u'), # if not in LUT, use "u"!!!
        ext='fits',
        )
    new_fname = "{instrument}_{date}_{time}_{obstype}{proctype}{prodtype}.{ext}".format(**fields)
    return new_fname

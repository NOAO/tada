"Calculate new fits header values from existing and auxiliary values."

import datetime
import os.path
from . import dateobs as obs

#!def instrument_calc(orighdr):
#!    "Instrument specific calculations"
#!    calc = dict() # Fields to calculate
#!    instrument = orighdr['INSTRUME'].lower()
#!
#!    # e.g. OBSID = 'kp4m.20141114T122626'
#!    # e.g. OBSID = 'soar.sam.20141220T015929.7Z'
#!    #!tele, dt_str = orighdr['OBSID'].split('.')
#!    
#!    if 'cosmos' == instrument:
#!        tele, dt_str = orighdr['OBSID'].split('.')
#!        #!datestr, _ = dt_str.split('T')
#!        calc['DTTELESC'] = tele
#!    elif 'mosaic1.1' == instrument:
#!        tele, dt_str = orighdr['OBSID'].split('.')
#!        #!datestr, _ = dt_str.split('T')
#!        calc['DTTELESC'] = tele
#!    elif 'soi' == instrument:
#!        tele, inst, dt_str1, dt_str2 = orighdr['OBSID'].split('.')
#!        #!dt_str = dt_str1 + dt_str2
#!        #!datestr, _ = dt_str.split('T')
#!        calc['DTTELESC'] = tele
#!    elif '90prime' == instrument: # BOK
#!        # FILENAME= 'bokrm.20140425.0119.fits' / base filename at acquisition
#!        tele = orighdr.get('TELESCOP', None)
#!        if tele == None:
#!            tele, datestr, *rest = orighdr['FILENAME'].split('.')
#!        calc['DTTELESC'] = tele
#!        calc['OBSTYPE'] = orighdr.get('IMAGETYP','object')
#!    else:
#!        pass
#!
#!    calc['DTINSTRU'] = instrument # eg. 'NEWFIRM'
#!    return calc

    

def calc_hdr(orighdr, fname, **kwargs):
    chg = dict() # Fields to change/add
    
    chg['TADAVERS']    = '0.0.dev5' # NOT REQUIRED, for diagnostics

    #! chg['DTTITLE']  = 'Not derivable from raw metadata!!!'
    #! chg['DTPIAFFL'] = 'Not derivable from raw metadata!!!'


    #!if 'COSMOS' == instrument:
    #!    tele, dt_str = orighdr['OBSID'].split('.')
    #!    datestr, _ = dt_str.split('T')
    #!elif 'Mosaic1.1' == instrument:
    #!    tele, dt_str = orighdr['OBSID'].split('.')
    #!    datestr, _ = dt_str.split('T')
    #!elif 'SOI' == instrument:
    #!    tele, inst, dt_str1, dt_str2 = orighdr['OBSID'].split('.')
    #!    dt_str = dt_str1 + dt_str2
    #!    datestr, _ = dt_str.split('T')
    #!elif '90Prime' == instrument: # BOK
    #!    # FILENAME= 'bokrm.20140425.0119.fits' / base filename at acquisition
    #!    tele, datestr, *rest = orighdr['FILENAME'].split('.')

    chg.update(instrument_calc(orighdr))
    
    
    #!# "UTC epoch"
    #!if 'T' in orighdr['DATE-OBS']: 
    #!    fmt = '%Y-%m-%dT%H:%M:%S.%f' 
    #!    dateobs = datetime.datetime.strptime(orighdr['DATE-OBS'],fmt)
    #!else:
    #!    fmt = '%Y-%m-%d'
    #!    dateobs = datetime.datetime.strptime(orighdr['DATE-OBS'][:10],fmt)

    #!dateobs = obs.parse_dateobs(orighdr['DATE-OBS'])
    dateobs = obs.normalize_dateobs(orighdr)
    
    #!chg['DTCOPYRI'] = 'AURA'                   # move to POSTPROC!!!
    #!chg['DTACQNAM'] = os.path.basename(fname)  # move to POSTPROC!!!
    #!chg['DTNSANAM'] = os.path.basename(fname)  # move to POSTPROC!!!

    #!chg['PROPOSER'] = orighdr['PROPID'] #!!!
    chg['DTPROPID'] = orighdr['PROPID'] 

    #! chg['DTPI']     = orighdr.get('PROPOSER', orighdr['PROPID'])
    #! chg['DTSITE']   = orighdr['OBSERVAT'].lower()
    #! chg['DTPUBDAT'] = 'NA' # doc says its required, cooked file lacks it

    # DTUTC cannot be derived exactly from any RAW fields
    # Should be: "post exposure UTC epoch from DTS"
    #!chg['DTUTC']    = dateobs.strftime('%Y-%m-%dT%H:%M:%S') #slightly wrong!!!
    chg['DTUTC']    = dateobs.isoformat()

    #! dir1 = datestr
    #! dir2 = tele
    #! dir3 = orighdr['PROPID']
    #! chg['SB_DIR1'] = dir1
    #! chg['SB_DIR2'] = dir2 
    #! chg['SB_DIR3'] = dir3
    # e.g. SB_DIR1='20141113', SB_DIR2='kp4m', SB_DIR3='2013B-0236'

    return chg, dateobs

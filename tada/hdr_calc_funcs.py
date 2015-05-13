'''Functions intended to be referenced in Personality files. 

Each function accepts a dictionary of name/values (intended to be from
a FITS header) and returns a dictionary of new name/values.  Fields
(names) may be added but not removed in the new dictionary with
respect to the original. To update the original dict, use python dict update:
   orig.update(new)

In each function of this file:
  orig::    orginal header as a dictionary
  RETURNS:: dictionary that should be used to update the header

'''

import logging

def addTimeToDATEOBS(orig):
    'Use TIME-OBS for time portion of DATEOBS.'
    new = {'ODATEOBS': orig['DATE-OBS'],                         # save original
           'DATE-OBS': orig['DATE-OBS'] + 'T' + orig['TIME-OBS']
           }
    return new
        

#DATEOBS is UTC, so convert DATEOBS to localdate and localtime, then:
#if [ $localtime > 12:00]; then DTCALDAT=localdate; else DTCALDAT=localdate-1 
def DTCALDATfromDATEOBS(orig):
    logging.error('STUB: DTCALDATfromDATEOBS!!!')
    localdate = orig['DATE-OBS']  # WRONG!!! (local <- UTC)
    new = {'DTCALDAT': localdate}
    return new

def DTTELESCfromINSTRUME(orig):
    "Instrument specific calculations"
    new = dict() # Fields to calculate
    instrument = orig['INSTRUME'].lower()

    # e.g. OBSID = 'kp4m.20141114T122626'
    # e.g. OBSID = 'soar.sam.20141220T015929.7Z'
    #!tele, dt_str = orighdr['OBSID'].split('.')
    
    if 'cosmos' == instrument:
        tele, dt_str = orig['OBSID'].split('.')
        new['DTTELESC'] = tele
    elif 'mosaic1.1' == instrument:
        tele, dt_str = orig['OBSID'].split('.')
        new['DTTELESC'] = tele
    elif 'soi' == instrument:
        tele, inst, dt_str1, dt_str2 = orig['OBSID'].split('.')
        new['DTTELESC'] = tele
#!    elif '90prime' == instrument: # BOK
#!        # FILENAME= 'bokrm.20140425.0119.fits' / base filename at acquisition
#!        tele = orig.get('TELESCOP', None)
#!        if tele == None:
#!            tele, datestr, *rest = orig['FILENAME'].split('.')
#!        new['DTTELESC'] = tele
#!        new['OBSTYPE'] = orig.get('IMAGETYP','object')
    else:
        pass

    new['DTINSTRU'] = instrument # eg. 'NEWFIRM'
    return new


    
def PROPIDtoDT(orig):
    new = {'DTPROPID': orig['PROPID'],  }
    return new

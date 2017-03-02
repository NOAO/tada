'''Functions intended to be referenced in Personality files. 

Each function accepts a dictionary of name/values (intended to be from
a FITS header) and returns a dictionary of new name/values.  Fields
(names) may be added but not removed in the new dictionary with
respect to the original. To update the original dict, use python dict update:
   orig.update(new)

In each function of this file:
  orig::    orginal header as a dictionary
  RETURNS:: dictionary that should be used to update the header

These function names MUST NOT CONTAIN UNDERSCORE ("_").  They are
listed by name in option values passed to "lp". Then underscores are
expanded to spaces to handle the command line argument limitation.

'''

import logging
#!from dateutil import tz
#!import datetime as dt
#!from . import hdr_calc_utils as hcu
#!from . import exceptions as tex

# Add fields to this list that are used by at least one hdr_func
# (unless they are already required in fits_utils:FILENAME_REQUIRED_FIELDS.)
#
#! calc_func_source_fields = set([
#!     'UTSHUT', 'INSTRUM', 'INSTRUME',
#!     'DATE-OBS', 'DATE', 'TIME-OBS',
#!     'IMAGETYP',
#!     'DETSERNO', 'DTSERNO',
#!     #'OBSTYPE',
#!     #'OBSID',
#! ])
#!
    
##############################################################################
#! 
#! def DETSERNOtoDTSERNO(orig, **kwargs):
#!     """Intended for soar-spartan FITS files."""
#!     if 'DETSERNO' in orig:
#!         return {'DTSERNO': orig['DETSERNO'].strip()}
#!     return dict()
#! 
#! def fixTriplespec(orig, **kwargs):
#!     new = {'DATE-OBS': orig['UTSHUT'],
#!            #'INSTRUME': orig['INSTRUM'],
#!     }
#!     logging.debug('fixTriplespec: fields DATE-OBS ({})'
#!                   #', INSTRUME ({})'
#!                   #.format(new['DATE-OBS'], new['INSTRUME']))
#!                   .format(new['DATE-OBS']))
#!     return  new
#! 
#! #!def trustSchedOrAAPropid(orig, **kwargs):
#! #!    '''Propid from schedule trumps header.  
#! #!But if not found in schedule, use field AAPROPID from header'''
#! #!    deprecate('trustSchedorAAPPropid')
#! #!    return {}
#! 
#! def addTimeToDATEOBS(orig, **kwargs):
#!     'Use TIME-OBS for time portion of DATEOBS. Depends on: DATE-OBS, TIME-OBS'
#!     if ('T' in orig['DATE-OBS']):
#!         new = dict()
#!     else:
#!         if 'ODATEOBS' in orig:
#!             logging.warning('Overwriting existing ODATEOBS!')
#!         new = {'ODATEOBS': orig['DATE-OBS'],            # save original
#!                'DATE-OBS': orig['DATE-OBS'] + 'T' + orig['TIME-OBS']
#!            }
#!     return new
#! 
#! def DATEOBSfromDATE(orig, **kwargs):
#!     if 'ODATEOBS' in orig:
#!         logging.warning('Overwriting existing ODATEOBS!')
#!     return {'ODATEOBS': orig['DATE-OBS'],            # save original
#!             'DATE-OBS': orig['DATE']+'.0' }
#! 
#! #DATEOBS is UTC, so convert DATEOBS to localdate and localtime, then:
#! #if [ $localtime > 9:00]; then DTCALDAT=localdate; else DTCALDAT=localdate-1
#! def DTCALDATfromDATEOBStus(orig, **kwargs):
#!     'Depends on: DATE-OBS'
#!     local_zone = tz.gettz('America/Phoenix')
#!     utc = dt.datetime.strptime(orig['DATE-OBS'], '%Y-%m-%dT%H:%M:%S.%f')
#!     utc = utc.replace(tzinfo=tz.tzutc()) # set UTC zone
#!     localdt = utc.astimezone(local_zone)
#!     if localdt.time().hour > 9:
#!         caldate = localdt.date()
#!     else:
#!         caldate = localdt.date() - dt.timedelta(days=1)
#!     #!logging.debug('localdt={}, DATE-OBS={}, caldate={}'
#!     #!              .format(localdt, orig['DATE-OBS'], caldate))
#!     new = {'DTCALDAT': caldate.isoformat()}
#!     return new
#! 
#! 
#! def DTCALDATfromDATEOBSchile(orig, **kwargs):
#!     'Depends on: DATE-OBS'
#!     local_zone = tz.gettz('Chile/Continental')
#!     utc = dt.datetime.strptime(orig['DATE-OBS'], '%Y-%m-%dT%H:%M:%S.%f')
#!     utc = utc.replace(tzinfo=tz.tzutc()) # set UTC zone
#!     localdt = utc.astimezone(local_zone)
#!     if localdt.time().hour > 12:
#!         caldate = localdt.date()
#!     else:
#!         caldate = localdt.date() - dt.timedelta(days=1)
#!     logging.debug('localdt={}, DATE-OBS={}, caldate={}'
#!                   .format(localdt, orig['DATE-OBS'], caldate))
#!     new = {'DTCALDAT': caldate.isoformat()}
#!     return new
#! 
#! def PROPIDplusCentury(orig, **kwargs):
#!     'Depends on: PROPID. Add missing century'
#!     return {'DTPROPID': '20' + orig.get('PROPID','NA').strip('"') }
#! 
#! def INSTRUMEtoDT(orig, **kwargs):
#!     'Depends on: INSTRUME'
#!     if 'DTINSTRU' in orig:
#!         return {'DTINSTRU': orig['DTINSTRU'] }
#!     else:
#!         return {'DTINSTRU': orig['INSTRUME'] }
#! 
#! 
#! def IMAGTYPEtoOBSTYPE(orig, **kwargs):
#!     'Depends on: IMAGETYP'
#!     return {'OBSTYPE': orig['IMAGETYP']  }
#! 
#! 
#! def bokOBSID(orig, **kwargs):
#!     "Depends on DATE-OBS"
#!     return {'OBSID': 'bok23m.'+orig['DATE-OBS'] }
#! 



    


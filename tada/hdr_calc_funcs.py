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
#!import urllib.request
import requests
from dateutil import tz
import datetime as dt
#from . import hdr_calc_utils as ut
from . import exceptions as tex

calc_func_source_fields = set([
    'UTSHUT', 'INSTRUM', 'INSTRUME',
    'DATE-OBS', 'DATE', 'TIME-OBS',
    'IMAGETYP',
    #'OBSTYPE',
    #'OBSID',
])

##############################################################################

# propid=`curl 'http://127.0.0.1:8000/schedule/propid/kp4m/kosmos/2016-02-01/'`
def http_get_propids_from_schedule(telescope, instrument, date,
                                  host=None, port=8000):
    '''Use MARS web-service to get PROPIDs given: Telescope, Instrument,
    Date of observation.  There will be multiple propids listed on split nights.
    '''
    url = ('http://{}:{}/schedule/propid/{}/{}/{}/'
           .format(host, port, telescope, instrument, date))
    logging.debug('MARS: get PROPID from schedule; url = {}'.format(url))
    propids = []
    try:
        #!with urllib.request.urlopen(url,timeout=6) as f:
        #!    response = f.read().decode('utf-8')
        r = requests.get(url, timeout=6)
        response = r.text
        logging.debug('MARS: server response="{}"'.format(response))
        propids = [pid.strip() for pid in response.split(',')]
        return propids
    except Exception as ex:
        logging.error('MARS: Error contacting schedule service via {}; {}'
                      .format(url, ex))
        return []
    return propids # Should never happen

def ws_lookup_propids(date, telescope, instrument, **kwargs):
    """Return propids from schedule (list of one or more)
-OR- None if cannot reach service
-OR- 'NA' if service reachable but lookup fails."""
    logging.debug('ws_lookup_propids; kwargs={}'.format(kwargs))
    host=kwargs.get('mars_host')
    port=kwargs.get('mars_port')
    if host == None or port == None:
        logging.error('Missing MARS host ({}) or port ({}).'.format(host,port))
        return []

    # telescope, instrument, date = ('kp4m', 'kosmos', '2016-02-01')
    logging.debug('WS schedule lookup; '
                  'DTCALDAT="{}", DTTELESC="{}", DTINSTRU="{}"'
                  .format(date, telescope, instrument))
    propids = http_get_propids_from_schedule(telescope, instrument, date,
                                             host=host, port=port)
    return propids

def deprecate(funcname, *msg):
    logging.warning('Using deprecated hdr_calc_func: {}'
                    .format(funcname, msg))
    
##############################################################################

def fixTriplespec(orig, **kwargs):
    new = {'DATE-OBS': orig['UTSHUT'],
           #'INSTRUME': orig['INSTRUM'],
    }
    logging.debug('fixTriplespec: fields DATE-OBS ({})'
                  #', INSTRUME ({})'
                  #.format(new['DATE-OBS'], new['INSTRUME']))
                  .format(new['DATE-OBS']))
    return  new

    
#!def trustHdrPropid(orig, **kwargs):
#!    deprecate('trustHdrPropid', 'Now we ALWAYS trust schedule.')
#!    return {}

#!    propid = orig.get('DTPROPID')
#!    if propid == 'BADSCRUB':
#!        # fallback
#!        propids = ws_lookup_propids(orig.get('DTCALDAT'),
#!                                    orig.get('DTTELESC'),
#!                                    orig.get('DTINSTRU'),
#!                                    **kwargs)
#!        if propids == None:
#!            return {}
#!        elif len(propids) > 1:
#!            return {'DTPROPID': 'SPLIT'}
#!        else:
#!            return {'DTPROPID': propids[0]}
#!    else:
#!        return {'DTPROPID': propid}

# MOVED TO FITS_UTILS: def set_dtpropid(orig, **kwargs):


#!def trustSchedPropid(orig, **kwargs):
#!    '''Propid from schedule trumps header.  
#!But if not found in schedule, use header'''
#!    deprecate('trustSchedPropid')
#!    return {}
#!
#!    pids = ws_lookup_propids(orig.get('DTCALDAT'),
#!                             orig.get('DTTELESC'),
#!                             orig.get('DTINSTRU'),
#!                             **kwargs)
#!    if pids == None:
#!        return {'DTPROPID': 'NOSCHED'}
#!    elif pids == 'NA':
#!        return {'DTPROPID': orig.get('DTPROPID',
#!                                     orig.get('PROPID', 'MISSCHED'))}
#!    elif len(pids) > 1:
#!        return {'DTPROPID': 'SPLIT'}
#!    else:
#!        return {'DTPROPID': pids[0]}

def trustSchedOrAAPropid(orig, **kwargs):
    '''Propid from schedule trumps header.  
But if not found in schedule, use field AAPROPID from header'''
    deprecate('trustSchedorAAPPropid')
    return {}
    #!pids = ws_lookup_propids(orig.get('DTCALDAT'),
    #!                         orig.get('DTTELESC'),
    #!                         orig.get('DTINSTRU'),
    #!                         **kwargs)
    #!if pids == None:
    #!    return {'DTPROPID': 'NOSCHED'}
    #!elif pids == 'NA':
    #!    return {'DTPROPID': orig.get('AAPROPID', 'na')}
    #!elif len(pids) > 1:
    #!    return {'DTPROPID': 'SPLIT'}
    #!else:
    #!    return {'DTPROPID': pids[0]}


    
def addTimeToDATEOBS(orig, **kwargs):
    'Use TIME-OBS for time portion of DATEOBS. Depends on: DATE-OBS, TIME-OBS'
    if ('T' in orig['DATE-OBS']):
        new = dict()
    else:
        if 'ODATEOBS' in orig:
            logging.warning('Overwriting existing ODATEOBS!')
        new = {'ODATEOBS': orig['DATE-OBS'],            # save original
               'DATE-OBS': orig['DATE-OBS'] + 'T' + orig['TIME-OBS']
           }
    return new

def DATEOBSfromDATE(orig, **kwargs):
    if 'ODATEOBS' in orig:
        logging.warning('Overwriting existing ODATEOBS!')
    return {'ODATEOBS': orig['DATE-OBS'],            # save original
            'DATE-OBS': orig['DATE']+'.0' }

#DATEOBS is UTC, so convert DATEOBS to localdate and localtime, then:
#if [ $localtime > 9:00]; then DTCALDAT=localdate; else DTCALDAT=localdate-1
def DTCALDATfromDATEOBStus(orig, **kwargs):
    'Depends on: DATE-OBS'
    local_zone = tz.gettz('America/Phoenix')
    utc = dt.datetime.strptime(orig['DATE-OBS'], '%Y-%m-%dT%H:%M:%S.%f')
    utc = utc.replace(tzinfo=tz.tzutc()) # set UTC zone
    localdt = utc.astimezone(local_zone)
    if localdt.time().hour > 9:
        caldate = localdt.date()
    else:
        caldate = localdt.date() - dt.timedelta(days=1)
    #!logging.debug('localdt={}, DATE-OBS={}, caldate={}'
    #!              .format(localdt, orig['DATE-OBS'], caldate))
    new = {'DTCALDAT': caldate.isoformat()}
    return new


def DTCALDATfromDATEOBSchile(orig, **kwargs):
    'Depends on: DATE-OBS'
    local_zone = tz.gettz('Chile/Continental')
    utc = dt.datetime.strptime(orig['DATE-OBS'], '%Y-%m-%dT%H:%M:%S.%f')
    utc = utc.replace(tzinfo=tz.tzutc()) # set UTC zone
    localdt = utc.astimezone(local_zone)
    if localdt.time().hour > 12:
        caldate = localdt.date()
    else:
        caldate = localdt.date() - dt.timedelta(days=1)
    logging.debug('localdt={}, DATE-OBS={}, caldate={}'
                  .format(localdt, orig['DATE-OBS'], caldate))
    new = {'DTCALDAT': caldate.isoformat()}
    return new

def PROPIDplusCentury(orig, **kwargs):
    'Depends on: PROPID. Add missing century'
    return {'DTPROPID': '20' + orig.get('PROPID','NA').strip('"') }

def INSTRUMEtoDT(orig, **kwargs):
    'Depends on: INSTRUME'
    if 'DTINSTRU' in orig:
        return {'DTINSTRU': orig['DTINSTRU'] }
    else:
        return {'DTINSTRU': orig['INSTRUME'] }


def IMAGTYPEtoOBSTYPE(orig, **kwargs):
    'Depends on: IMAGETYP'
    return {'OBSTYPE': orig['IMAGETYP']  }


def bokOBSID(orig, **kwargs):
    "Depends on DATE-OBS"
    return {'OBSID': 'bok23m.'+orig['DATE-OBS'] }

#! def DTTELESCfromINSTRUME(orig, **kwargs):
#!     "Instrument specific calculations. Depends on: INSTRUME, OBSID"
#!     new = dict() # Fields to calculate
#!     instrument = orig['INSTRUME'].lower()
#! 
#!     # e.g. OBSID = 'kp4m.20141114T122626'
#!     # e.g. OBSID = 'soar.sam.20141220T015929.7Z'
#!     #!tele, dt_str = orighdr['OBSID'].split('.')
#!     if 'cosmos' == instrument:
#!         tele, dt_str = orig['OBSID'].split('.')
#!         new['DTTELESC'] = tele
#!     elif 'mosaic1.1' == instrument:
#!         tele, dt_str = orig['OBSID'].split('.')
#!         new['DTTELESC'] = tele
#!     elif 'soi' == instrument:
#!         tele, inst, dt_str1, dt_str2 = orig['OBSID'].split('.')
#!         new['DTTELESC'] = tele
#! #!    elif '90prime' == instrument: # BOK
#! #!        # FILENAME='bokrm.20140425.0119.fits' / base filename at acquisition
#! #!        tele = orig.get('TELESCOP', None)
#! #!        if tele == None:
#! #!            tele, datestr, *rest = orig['FILENAME'].split('.')
#! #!        new['DTTELESC'] = tele
#! #!        new['OBSTYPE'] = orig.get('IMAGETYP','object')
#! #!    else:
#! #!        tele, dt_str = orig['OBSID'].split('.')
#! #!        new['DTTELESC'] = tele
#! 
#!     #! new['DTINSTRU'] = instrument # eg. 'NEWFIRM'
#!     return new


    

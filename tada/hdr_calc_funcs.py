>'''Functions intended to be referenced in Personality files. 

Each function accepts a dictionary of name/values (intended to be from
a FITS header) and returns a dictionary of new name/values.  Fields
(names) may be added but not removed in the new dictionary with
respect to the original. To update the original dict, use python dict update:
   orig.update(new)

In each function of this file:
  orig::    orginal header as a dictionary
  RETURNS:: 
    updict:: dictionary that should be used to update the header
    delfields:: fields that should be deleted from header

These function names MUST NOT CONTAIN UNDERSCORE ("_").  They are
listed by name in option values passed to "lp". Then underscores are
expanded to spaces to handle the command line argument limitation.

'''

import logging
import requests
import datetime as dt
from dateutil import tz
from . import exceptions as tex
from . import settings

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
    host=settings.mars_host
    port=settings.mars_port
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

def hist_change(field, old, new):
    msg = 'Changed field "{}" from "{}" to "{}"'.format(field, old, new)
    return msg

##############################################################################
### MAPPING FUNCTIONS
###

def fixTriplespec(orig, **kwargs):
    new = {'DATE-OBS': orig['UTSHUT'],
           #'INSTRUME': orig['INSTRUM'],
    }
    logging.debug('fixTriplespec: fields DATE-OBS ({})'
                  #', INSTRUME ({})'
                  #.format(new['DATE-OBS'], new['INSTRUME']))
                  .format(new['DATE-OBS']))
    return  new, dict()

    
def trustSchedOrAAPropid(orig, **kwargs):
    '''Propid from schedule trumps header.  
But if not found in schedule, use field AAPROPID from header'''
    deprecate('trustSchedorAAPPropid')
    return {}, dict()
    
def addTimeToDATEOBS(orig, **kwargs):
    'Use TIME-OBS for time portion of DATEOBS. Depends on: DATE-OBS, TIME-OBS'
    if ('T' in orig['DATE-OBS']):
        new = dict()
    else:
        oldval = orig.get('DATE-OBS','<NONE>')
        newval = orig['DATE-OBS'] + 'T' + orig['TIME-OBS']
        new = {'DATE-OBS': newval }
    change = dict(history = [hist_change('DATE-OBS', oldval, newval)])
    return new, change

def DATEOBSmicrosFromDETSERNO(orig, **kwargs):
    """Intended for soar-spartan FITS files."""
    history=dict()
    serno = orig.get('DETSERNO',None)
    if not serno:
        return dict(), dict()

    sn = serno.strip()
    oldval = orig['DATE-OBS']
    newval = orig['DATE-OBS'].split('.')[0] + '.' + sn
    change = dict(history = [hist_change('DATE-OBS', oldval, newval)])
    return {'DATE-OBS': newval}, change
    
def DATEOBSfromDATE(orig, **kwargs):
    oldval = orig.get('DATE-OBS','<NONE>')
    newval = orig['DATE']+'.0'
    change = dict(history = [hist_change('DATE-OBS', oldval, newval)])
    return {'DATE-OBS': newval }, change


def DATEOBStoISO(orig, **kwargs):
    oldval = orig.get('DATE-OBS','<NONE>')
    newval = orig['DATE-OBS'].replace(' ','T')
    change = dict(history = [hist_change('DATE-OBS', oldval, newval)])
    return {'DATE-OBS': newval}, change

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
    new = {'DTCALDAT': caldate.isoformat()}
    return new, dict()


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
    new = {'DTCALDAT': caldate.isoformat()}
    return new, dict()

def PROPIDplusCentury(orig, **kwargs):
    'Depends on: PROPID. Add missing century'
    return {'DTPROPID': '20' + orig.get('PROPID','NA').strip('"') }, dict()

def INSTRUMEtoDT(orig, **kwargs):
    'Depends on: INSTRUME'
    if 'DTINSTRU' in orig:
        return {'DTINSTRU': orig['DTINSTRU'] }, dict()
    else:
        return {'DTINSTRU': orig['INSTRUME'] }, dict()


def IMAGTYPEtoOBSTYPE(orig, **kwargs):
    'Depends on: IMAGETYP'
    return {'OBSTYPE': orig['IMAGETYP']  }, dict()


def bokOBSID(orig, **kwargs):
    "Depends on DATE-OBS"
    return {'OBSID': 'bok23m.'+orig['DATE-OBS'] }, dict()


    

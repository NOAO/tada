'''Clean the values for fields if possible.

All SCRUBBED functions ("scrub_FIELDNAME") have the same signature:
scrub_FIELDNAME(origValue,hdr) => goodValue
RETURN: None if value cannot be coerced to good value, else return good value.
SIDE-EFFECT; hdr may be modified
'''
import re
import datetime as dt
import time as tt
import logging
import collections




##############################################################################
### DTPROPID
###
# DTPROPID format: YYYY[AB]-NNNN or one of:
#  - wiyn
#  - noao
#  - soar
#  - smarts
# GOOD EXAMPLES:
#  2015B-0115
# BAD EXAMPLES
#  15B-0115


valid_dtpropids = set(['wiyn','noao','soar','smarts', 'tspec', 'BADSCRUB'])
propidRE = re.compile(r'20\d{2}[AB]-\d{4}')
def scrub_propid(value, hdr):
    #! logging.debug('DBG: scrub_propid({},{})'.format(value, hdr))
    if value in valid_dtpropids:
        return value
    if propidRE.match(value):
        return value

    if '20' != value[:2] and len(value) == 8:
        new = '20'+value
        if propidRE.match(new):
            return new
    # For Propid, we MAY do schedule lookup downstream. Always 
    # do lookup if DTPROPID=BADSCRUB.
    return 'BADSCRUB'



##############################################################################
### DATE-OBS
###
# See also: hdr_calc_funcs.py
#

## dateobs_values_from_past_hdrs = ['2014-04-25',
##                                  '2014-09-22T18:02:59',
##                                  '2004-10-16T19:53:04.0',
##                                  '2005-03-09T03:23:30.5',
##                                  '2014-12-22 12:53:01.211',
##                                  '2015-02-22T18:11:35.088305',
##                                  '2015-05-07T08:55:56.429488359',  ]

# This parses the known examples.  But its possible that DATE-OBS is
# "allowed" to be any ISO8601 date/time.  ISO allows LOTS of things
# that this won't catch. If we start getting very special (but still
# ISO) strings, consider using python:
#   dateutil, iso8601, or python-rfc3339
#
dateobsRE = re.compile(r'''
  (?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})  # date
  ((T|[ ])                     # date/time separator; "T" or space
   (?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})(?P<nano>\.\d+)? # time
  )?                           # time is optional
''', flags=re.VERBOSE)

# NB: value should be in UTC
def parse_dateobs(dtstr, timestr=None):
    'Return datetime object representing value of DATE-OBS'

    m = dateobsRE.match(dtstr)
    if not m:
        return None

    md = m.groupdict()    
    # "UTC epoch"
    #!if 'T' in hdr['DATE-OBS']: 
    #!    fmt = '%Y-%m-%dT%H:%M:%S.%f' 
    #!    dateobs = datetime.datetime.strptime(hdr['DATE-OBS'],fmt)
    #!elif ' ' in hdr['DATE-OBS']:
    #!    fmt = '%Y-%m-%d %H:%M:%S.%f' 
    #!    dateobs = datetime.datetime.strptime(hdr['DATE-OBS'],fmt)
    #!else:
    #!    fmt = '%Y-%m-%d'
    #!    dateobs = datetime.datetime.strptime(hdr['DATE-OBS'][:10],fmt)
    
    date = dt.date(int(md['year']), int(md['month']), int(md['day']))
    if md['hour']:
        nano = float(md['nano']) if md['nano'] else 0
        time = dt.time(int(md['hour']), int(md['min']), int(md['sec']), 0)
        return dt.datetime.combine(date,time)
    elif timestr != None:
        if len(timestr) > 8:
            return dt.datetime.strptime(dtstr + 'T' + timestr,
                                        '%Y-%m-%dT%H:%M:%S.%f')
        else:
            return dt.datetime.strptime(dtstr + 'T' + timestr,
                                        '%Y-%m-%dT%H:%M:%S')
    else:
        #!logging.warning('No TIME found in DATE-OBS ({}), using zeros.'
        #!                .format(dtstr))
        #!time = dt.time()
        return date

def validate_dateobs_content(dateobs, datestr):
    'DATE-OBS content: Correct century and Not Future'
    if str(dateobs.year)[:2] != '20':
        raise tex.BadFieldContent(
        'DATE-OBS is not current century.  Value={}' .format(datestr))
    if dateobs > dt.datetime.now():
        raise tex.BadFieldContent(
            'DATE-OBS is in the future.  Value={}'.format(datestr))
    return True    

def normalize_dateobs(hdr):
    '''Return a DATE-OBS value that always has the same format: 
yyyy-mm-ddThh:mm:ss.nnnnnnnnn'''

    #dateobs = dt.datetime.strptime(chg['DATE-OBS'],'%Y-%m-%dT%H:%M:%S.%f')    
    if 'DATE-OBS' not in hdr:
        return None
    hdr['ODATEOBS'] = hdr['DATE-OBS'] # save original

    #!if hdr.get('INSTRUME') == '90prime':
    #!    if 'TIME-OBS' not in hdr:
    #!        logging.error('INSTRUME=90prime contains DATE-OBS without TIME '
    #!                      'and to TIME-OBS exists to use for TIME.')
    #!        return None
    #!    else:
    #!        logging.warning('INSTRUME=90prime contains DATE-OBS without TIME '
    #!                        'so using TIME from TIME-OBS.')
    #!        dateobs = parse_dateobs('{}T{}'.format(hdr['DATE-OBS'],
    #!                                               hdr['TIME-OBS']))
    #!else:
    dateobs = parse_dateobs(hdr['DATE-OBS'], timestr=hdr.get('TIME-OBS'))

    #!dtstr = (dateobs+dt.timedelta(microseconds=1)).isoformat()
    dtstr = dateobs.isoformat()
    if dateobs.microsecond == 0:
        dtstr += '.0' # make parsing easier
    # dtstr => e.g. '2002-12-25T00:00:00.000001'
    validate_dateobs_content(dateobs, dtstr)
    hdr['DATE-OBS'] = dtstr   # save normalized version
    #!return dateobs
    return dtstr


def scrub_dateobs(UNUSED_value, hdr):
    return(normalize_dateobs(hdr))

##############################################################################
def scrub_hdr(hdr):
    'SIDE-EFFECT: hdr modified where fields need scrubbbing'
    errors = []
    for k,(func,newname,savename) in scrub_fields.items():
        origValue = hdr.get(k)
        if origValue == None:
            errors.append('No value found for field {} during scrub.'.format(k))
            continue
        goodValue = func(origValue, hdr)
        if goodValue == None:
            errors.append('Could not coerce {} to a good value for field {}'
                          .format(origValue,k))
        else:
            hdr[newname] = goodValue
            logging.debug('SCRUB: Setting {}= {}'.format(newname, goodValue))
            if goodValue != origValue and savename != None:
                hdr[savename] = origValue
    return errors


scrub_fields = collections.OrderedDict([
    # OrigName   Function          NewName      SaveName
    ('PROPID',   (scrub_propid,   'DTPROPID',   None      )),
    ('AAPROPID', (scrub_propid,   'DTPROPID',   None      )),
    ('DATE-OBS', (scrub_dateobs,  'DATE-OBS',  'ODATEOBS' )),
])


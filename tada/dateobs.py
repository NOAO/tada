"Normalize the DATE-OBS field in a FITS header."

import re
import datetime as dt
import logging

example_values = [
    '2014-04-25',
    '2014-09-22T18:02:59',
    '2004-10-16T19:53:04.0',
    '2005-03-09T03:23:30.5',
    '2014-12-22 12:53:01.211',     
    '2015-02-22T18:11:35.088305',
    '2015-05-07T08:55:56.429488359',
    ]
#!example_values.append(None)


# This parses the known examples.  But its possible that DATE-OBS is
# "allowed" to be any ISO8601 date/time.  ISO allows LOTS of things
# that this won't catch. If we start getting very special (but still
# ISO) strings, consider using python:
#   dateutil, iso8601, or python-rfc3339
#
dateRE = re.compile(r'''
  (?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})  # date
  ((T|[ ])                     # date/time separator; "T" or space
   (?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})(?P<nano>\.\d+)? # time
  )?                           # time is optional
''', flags=re.VERBOSE)

# NB: value should be in UTC
def parse_dateobs(dtstr):
    'Return datetime object representing value of DATE-OBS'

    m = dateRE.match(dtstr)
    if not m:
        # !!! throw exception? 
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

    else:
        logging.warning('No TIME found in DATE-OBS ({}), using zeros.'
                        .format(dtstr))
        time = dt.time()
    return dt.datetime.combine(date,time)

def normalize_dateobs(hdr):
    '''Return a DATE-OBS value that always has the same format: 
yyyy-mm-ddThh:mm:ss.nnnnnnnnn'''

    if 'DATE-OBS' not in hdr:
        return None
    hdr['ODATEOBS'] = hdr['DATE-OBS'] # save original

    if hdr['INSTRUME'] == '90prime':
        logging.warning('INSTRUME=90prime contains DATE-OBS without TIME '
                        'so using TIME from TIME-OBS.')
        dateobs = parse_dateobs('{}T{}'.format(hdr['DATE-OBS'], hdr['TIME-OBS']))
    else:
        dateobs = parse_dateobs(hdr['DATE-OBS'])

    dtstr = dateobs.isoformat()
    hdr['DATE-OBS'] = dtstr   # save normalized version
    return dateobs

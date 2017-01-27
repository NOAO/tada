'Utility functions used by functions in hdr_calc_funcs.'
import logging
import pkg_resources
import datetime
import requests
from . import settings

class HeaderChange():
    """Accumulate changes that will eventually be made to a FITS header.
Changes may include:
  - change field values
  - delete fields
  - addition to HISTORY
  - addition to COMMENT

orig:: the original FITS header as dict
"""
    def __init__(self, origdict, **kwargs):
        self.orig = origdict.copy()
        self.new = origdict.copy() 
        self.removekeys = list()
        self.history = list()
        self.comment = list()

    def change(self, key, newvalue):
        self.new[key] = newvalue
        
    def apply(self, fitsheader):
        fitsheader['HISTORY'] = ('TADA modified header on: {}'
                                 .format(datetime.datetime.now().isoformat()))
        # pylint: disable=no-member
        vers = pkg_resources.get_distribution('tada').version
        fitsheader['HISTORY'] = 'TADA version: {}'.format(vers)

        # Change values and record change in history
        for k,val in self.new.items():
            hist = ('Changed key ({}) from value ({}) to ({}).'
                    .format(k,
                            fitsheader.get(k,'<none>'),
                            val))
            fitsheader[k] = val
            fitsheader['HISTORY'] = hist

        # Delete keys and record change in history
        for kw in self.removekeys:
            hist = ('Removed key ({}) with value ({}).'
                    .format(kw, fitsheader[kw]))
            fitsheader['HISTORY'] = hist
            del fitsheader[kw]

        # Add additional HISTORY and COMMENT cards
        for s in self.history:
            fitsheader['HISTORY'] = s
        for s in self.comment:
            fitsheader['COMMENT'] = s
            
        return fitsheader

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
    logging.warning('Using deprecated hdr_calc_func: {}; {}'
                    .format(funcname, msg))
    

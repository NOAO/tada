'Utility functions used by functions in hdr_calc_funcs.'
import logging
import requests
from . import settings


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
    

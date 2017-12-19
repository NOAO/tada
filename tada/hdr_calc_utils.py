'Utility functions used by functions in hdr_calc_funcs.'
import logging
import requests
from . import settings
from . import exceptions as tex

##############################################################################

# propid=`curl 'http://127.0.0.1:8000/schedule/propid/kp4m/kosmos/2016-02-01/'`
def http_get_propid_for_db(telescope, instrument, date, hdrpid,
                           timeout=10, #secs to wait for any bytes
                           host=None, port=8000) :
    '''Use MARS web-service to get PROPID to use in DB 
given: Telescope, Instrument, Date of observation.  
    '''
    url = ('http://{}:{}/schedule/dbpropid/{}/{}/{}/{}/'
           .format(host, port, telescope, instrument, date, hdrpid))
    logging.debug('MARS: get PROPID from schedule; url = {}'.format(url))
    pid = None
    r = requests.get(url, timeout=timeout)
    response = r.text
    logging.debug('MARS: server response="{}"'.format(response))
    if r.status_code == 200:
        logging.debug('MARS: server status ok')
        return response
    else:
        msg = ('{}:MARS svc={}; {}.'
               .format(r.status_code, url.replace(host,'mars.host'), response))
        logging.info(msg)
        raise tex.MarsWebserviceError(response)


def ws_get_propid(date, telescope, instrument, hdr_pid):
    """Return propid suitiable for use in DB."""
    host=settings.mars_host
    port=settings.mars_port
    if host == None or port == None:
        msg = 'Missing MARS host ({}) or port ({}).'.format(host,port)
        logging.info(msg)
        raise tex.MarsWebserviceError(msg)

    # telescope, instrument, date = ('kp4m', 'kosmos', '2016-02-01')
    logging.debug('WS schedule lookup; '
                  'DTCALDAT="{}", DTTELESC="{}", DTINSTRU="{}"'
                  .format(date, telescope, instrument))
    try:
        pid = http_get_propid_for_db(telescope, instrument, date, hdr_pid,
                                     host=host, port=port)
    except Exception as err:
        msg = ('Failed Propid lookup '
               'tele={}, instr={}, date={}, hdrpid={}; {}')\
               .format(telescope, instrument, date, hdr_pid, err)
        logging.info(msg)
        raise tex.MarsWebserviceError(err)
    return pid

# propid=`curl 'http://127.0.0.1:8000/schedule/propid/kp4m/kosmos/2016-02-01/'`
def http_get_propids_from_schedule(telescope, instrument, date,
                                   timeout=10, #secs to wait for any bytes
                                   host=None, port=8000,
                                   ):
    '''Use MARS web-service to get PROPIDs given: Telescope, Instrument,
    Date of observation.  There will be multiple propids listed on split nights.
    '''
    url = ('http://{}:{}/schedule/propid/{}/{}/{}/'
           .format(host, port, telescope, instrument, date))
    logging.debug('MARS: get PROPID from schedule; url = {}'.format(url))
    propids = []
    try:
        r = requests.get(url, timeout=timeout)
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
    """Return a list of propids from schedule (list of one or more)
-OR- [] if cannot reach service
-OR- ['NEED-DEFAULT.'<tel>.<inst>] if service reachable but lookup fails."""
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
    if propids[0][:15] == '<!DOCTYPE html>':
        logging.error('WS schedule lookup returned HTML')
        return []
    else:
        return propids

def deprecate(funcname, *msg):
    logging.warning('Using deprecated hdr_calc_func: {}; {}'
                    .format(funcname, msg))
    

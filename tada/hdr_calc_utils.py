'Utility functions used by functions in hdr_calc_funcs.'
import logging
import urllib.request

# propid=`curl 'http://127.0.0.1:8000/schedule/propid/kp4m/kosmos/2016-02-01/'`
def http_get_propid_from_schedule(telescope, instrument, date,
                                  host=None, port=8000):
    'Use MARS web-service to get PROPID given: Telescope, Date of observation.'
    url = ('http://{}:{}/schedule/propid/{}/{}/{}/'
           .format(host, port, telescope, instrument, date))
    logging.debug('MARS: get PROPID from schedule; url = {}'.format(url))
    propid = None
    try:
        with urllib.request.urlopen(url,timeout=6) as f:
            response = f.read().decode('utf-8')
            logging.debug('MARS: server response="{}"'.format(response))
            return response
    except:
        logging.error('MARS: Error contacting schedule service via {}'
                      .format(url))
        return None
    return propid

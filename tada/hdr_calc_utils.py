'Utility functions used by functions in hdr_calc_funcs.'
import logging
import urllib.request

# propid=`curl 'http://127.0.0.1:8000/schedule/prop/ct13m/2014-12-25/'`
def http_get_propid_from_schedule(telescope, date, host=None, port=8000):
    'Use MARS web-service to get PROPID given: Telescope, Date of observation.'
    url = ('http://{}:{}/schedule/propid/{}/{}/'
           .format(host, port, telescope, date))
    logging.debug('MARS: PROPID from schedule; url = {}'.format(url))
    response = ''
    try:
        with urllib.request.urlopen(url,timeout=4) as f:
            response = f.read().decode('utf-8')
            logging.debug('MARS: server response: {}'.format(response))
            
    except:
        logging.error('MARS: Could not retrieve DTPROPID from schedule using {}'
                      .format(url))
    propid = 'NOSCHED' if response == '' else response
    return propid

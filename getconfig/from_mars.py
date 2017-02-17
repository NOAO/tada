"""Library for retrieving TADA config info from MARS.
"""

import json
import requests
import yaml
#!from tada import settings

def getMarsTadaJson(urlleaf):
    #!host=settings.mars_host
    #!port=settings.mars_port
    #url = 'http://{}:{}/tada/{}'.format(host,port, urlleaf)
    url = 'http://mars:8000/tada/{}'.format(urlleaf)
    try:
        r = requests.get(url)

    except Exception as ex:
        logging.error('MARS: Error contacting MARS service via {}; {}'
                      .format(url, ex))
        return
    return json.loads(r.text)

def genPrefixTable(yamlfilename):
    """Convert SiteTelescopeInstrument LUT from MARS into YAML."""
    jsondata = getMarsTadaJson('pfx')
    with open(yamlfilename, 'w') as yamlfile:
        yaml.dump(jsondata, yamlfile)
    return

def genObsTable(yamlfilename):
    """Convert MARS tada/obs web-service call into YAML."""
    jsondata = getMarsTadaJson('obs')
    with open(yamlfilename, 'w') as yamlfile:
        yaml.dump(jsondata, yamlfile)
    return

def genProcTable(yamlfilename):
    """Convert MARS tada/proc web-service call into YAML."""
    jsondata = getMarsTadaJson('proc')
    with open(yamlfilename, 'w') as yamlfile:
        yaml.dump(jsondata, yamlfile)
    return

def genProdTable(yamlfilename):
    """Convert MARS tada/prod web-service call into YAML."""
    jsondata = getMarsTadaJson('prod')
    with open(yamlfilename, 'w') as yamlfile:
        yaml.dump(jsondata, yamlfile)
    return

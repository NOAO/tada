"""Make sense of HTTP responses from Archive Ingest.
+++ Add to this to get better messages in TADA log when Archive Ingest fails.
"""

import re
import xml.etree.ElementTree as ET
import logging

'''
see:
- Jira, DEVEL-597
- http://nsabuild.tuc.noao.edu/projectdocs/services/dataproductload/report.html

<ingest type="FAILURE" dataProductUri="irods:///noao-tuc-z1/ingest-data/kp173541.hdr.gz">
  <message type="DP_ALREADY_IN_DB">
    <user>Header for reference:[kp173541.fits.gz] has already been stored in the database</user>
    <stacktrace>THIS WILL CONTAIN NEWLINES</stacktrace>
  </message>
</ingest>

'''

def decodeIngest(response):
    'response:: XML-string http-response from nsaarchive'

#!    # Handle old style response (from NSA version 2.4.0)
#!    if response[0] != "<":
#!        msg = decodeIngest_240(response)
#!        success = (response == "Success")
#!        return success, msg

    root = ET.fromstring(response)
    itype = root.get('type')
    #dpuri = root.get('dataProductUri')
    success = ((itype == 'SUCCESS') or (itype == 'SUCCESS_WITH_WARNING'))
    msg = '' if success else root.find('./message/user').text 
    #return success,'Operator:: ' + msg
    return success, msg, itype

###############################################################################

existsRE = re.compile(r"has already been stored in the database")
'''Failure reason:Failed to ingest
file:/noao-tuc-z1/tada/vagrant/5/k4n_20141114_122626_oru.hdr error
msg:Header for k4n_20141114_122626_oru.fits has already been stored in
the database'''

dup_propRE = re.compile(r"Could not find unique proposal")
'''Failure reason:Failed to ingest
file:/noao-tuc-z1/tada/vagrant/23/ksb_041016_195304_uuu_1188439357.hdr
error msg:Could not find unique proposal TEST-noao in metadata
database, found 0'''


dup_obspropRE = re.compile(r"Got more than one observation matching calibration date for proposal")
'''Failure reason:Failed to ingest
file:/noao-tuc-z1/tada/vagrant/2/k4k_140922_234549_zuu_1186823651.hdr
error msg:Got more than one observation matching calibration date for
proposal. Query: select distinct o from ObservationEntity o join fetch
o.proposalSet p where p.proposalId = ?1 and o.calibrationDate between
?2 and ?3 and o.publicDataReleaseDate < ?4'''

hdr_existsRE = re.compile(r"iRODS HDR file already exists at")
'''iRODS HDR file already exists at
/noao-tuc-z1/mtn/20160608/ct4m/NA/c4ai_160609_151943_ori.hdr on submit
of
/data1/tada/dropbox/20160609/ct4m-arcoiris/SPEC_FFtest0583.fits. Aborting
attempt to ingest.'''

prop_not_foundRE = re.compile(r"Could not find the proposal:")
'''Could not find the proposal:[NA] in the database.'''

nonfitsRE = re.compile(r"Cannot ingest non-FITS file:")
'''Cannot ingest non-FITS file:
/sandbox/tada/tests/smoke/tada-test-data/basic/uofa-mandle.jpg'''

missingreqRE = re.compile(r"header is missing required metadata fields")
'''Modified FITS header is missing required metadata fields (PROCTYPE, PRODTYPE) in file /sandbox/tada/tests/smoke/tada-test-data/basic/kptest.fits'''

baddateRE = re.compile(r"Could not parse DATE-OBS field")
'''Could not parse DATE-OBS field (2004-12-16) in header of: /sandbox/tada/tests/smoke/tada-test-data/basic/kp109391.fits.fz'''

# these must be searched in order. First MatchFunc to return True wins.
ERRMAP = [
    # ERRCODE,  MatchFunc, ShortDesc
    ('DUPFITS', existsRE.search,      'Already stored in Archive'),
    ('BADPROP', dup_propRE.search,    'Unique propid not found' ),
    ('COLLIDE', dup_obspropRE.search, 'Multi-files match date + propid'),
    ('NOPROP',  prop_not_foundRE.search, 'Propid not in Archive DB'),
    ('MISSREQ', missingreqRE.search,   'Missing required metadata'),
    ('BADDATE', baddateRE.search,     'DATE-OBS bad format'),
    ('NOTFITS', nonfitsRE.search,     'Cannot ingest non-FITS file'),
    ('none',    None,                 'No error'),
    ('UNKNOWN', None,                 'Unknown error'),
]


def errcode(response):
    if existsRE.search(response):
        return 'DUPFITS'
    elif dup_propRE.search(response):
        return 'BADPROP'
    elif dup_obspropRE.search(response):
        return 'COLLIDE'
    elif prop_not_foundRE.search(response):
        return 'NOPROP'
    elif missingreqRE.search(response):
        return 'MISSREQ'
    elif baddateRE.search(response):
        return 'BADDATE'
    elif nonfitsRE.search(response):
        return 'NOTFITS',
    elif len(response.strip()) == 0:
        return 'none'
    else:
        logging.error('errcode cannot code for error message: {}'
                      .format(response))
        return 'UNKNOWN'
    



    
#!    def decodeIngest_240(response):
#!        if existsRE.search(response):
#!            msg = ('Already in DB. To submit this file, '
#!                   'remove existing from DB and do: "dqcli --redo"')
#!        elif nonunique_propidRE.search(response):
#!            msg = ('Bad DTPROPID. To submit this file, '
#!                   'fix header or resubmit with "-o _DTPROPID=<propid>"')
#!        elif dup_obs_propRE.search(response):
#!            msg = ('Duplicate DTPROPID, DTCALDAT combination. '
#!                   'To submit this file, '
#!                   'fix header or resubmit with '
#!                   '"-o _DTPROPID=<propid> -o _DTCALDAT=<caldat>"')
#!        else:
#!            msg = '<no operator message in ingest_decoder.py::decodIngest()>'
#!        return 'Operator:: ' + msg

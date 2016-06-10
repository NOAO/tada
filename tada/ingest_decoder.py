"""Make sense of HTTP responses from Archive Ingest.
+++ Add to this to get better messages in TADA log when Archive Ingest fails.
"""

import re
import xml.etree.ElementTree as ET

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
    return success, msg

###############################################################################

class TadaErrors():
    exists_re = re.compile(r"has already been stored in the database")
    '''Failure reason:Failed to ingest
    file:/noao-tuc-z1/tada/vagrant/5/k4n_20141114_122626_oru.hdr error
    msg:Header for k4n_20141114_122626_oru.fits has already been stored in
    the database'''

    dup_prop_re = re.compile(r"Could not find unique proposal")
    '''Failure reason:Failed to ingest
    file:/noao-tuc-z1/tada/vagrant/23/ksb_041016_195304_uuu_1188439357.hdr
    error msg:Could not find unique proposal TEST-noao in metadata
    database, found 0'''


    dup_obsprop_re = re.compile(r"Got more than one observation matching calibration date for proposal")
    '''Failure reason:Failed to ingest
    file:/noao-tuc-z1/tada/vagrant/2/k4k_140922_234549_zuu_1186823651.hdr
    error msg:Got more than one observation matching calibration date for
    proposal. Query: select distinct o from ObservationEntity o join fetch
    o.proposalSet p where p.proposalId = ?1 and o.calibrationDate between
    ?2 and ?3 and o.publicDataReleaseDate < ?4'''

    hdr_exists_re = re.compile(r"iRODS HDR file already exists at")
    '''iRODS HDR file already exists at
    /noao-tuc-z1/mtn/20160608/ct4m/NA/c4ai_160609_151943_ori.hdr on submit
    of
    /data1/tada/dropbox/20160609/ct4m-arcoiris/SPEC_FFtest0583.fits. Aborting
    attempt to ingest.'''

    prop_not_found_re = re.compile(r"Could not find the proposal:")
    '''Could not find the proposal:[NA] in the database.'''

    # these must be searched in order. First MatchFunc to return True wins.
    ERRMAP = [
        # ERRCODE,  MatchFunc, ShortDesc
        ('DUPFITS', exists_re.search,      'Already stored in Archive'),
        ('BADPROP', dup_prop_re.search,    'Unique propid not found' ),
        ('COLLIDE', dup_obsprop_re.search,'Multi-files match date + propid'),
        ('UNKNOWN', None,                   'Unknown error'),
    ]


#!    def decodeIngest_240(response):
#!        if exists_re.search(response):
#!            msg = ('Already in DB. To submit this file, '
#!                   'remove existing from DB and do: "dqcli --redo"')
#!        elif nonunique_propid_re.search(response):
#!            msg = ('Bad DTPROPID. To submit this file, '
#!                   'fix header or resubmit with "-o _DTPROPID=<propid>"')
#!        elif dup_obs_prop_re.search(response):
#!            msg = ('Duplicate DTPROPID, DTCALDAT combination. '
#!                   'To submit this file, '
#!                   'fix header or resubmit with '
#!                   '"-o _DTPROPID=<propid> -o _DTCALDAT=<caldat>"')
#!        else:
#!            msg = '<no operator message in ingest_decoder.py::decodIngest()>'
#!        return 'Operator:: ' + msg

    def errcode(self, response):
        if self.exists_re.search(response):
            return 'DUPFITS'
        elif self.nonunique_propid_re.search(response):
            return 'BADPROP'
        elif self.dup_obs_prop_re.search(response):
            return 'COLLIDE'
        else:
            return 'UNKNOWN'
    


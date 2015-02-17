"""Make sense of HTTP responses from Archive Ingest.
+++ Add to this to get better messages in TADA log when Archive Ingest fails.
"""

import re

# "Failure reason:Failed to ingest file:/noao-tuc-z1/tada/vagrant/5/k4n_20141114_122626_oru.hdr error msg:Header for k4n_20141114_122626_oru.fits has already been stored in the database"
exists_re = re.compile(r"has already been stored in the database")
                       

def decodeIngest(response):
    if exists_re.search(response):
        msg = ('Already in DB. To submit this file, '
               'remove existing from DB and do: "dqcli --redo"')
    else:
        msg = '<none>'

    return 'Operator:: ' + msg


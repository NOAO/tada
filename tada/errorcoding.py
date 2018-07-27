"""\
Convert error TADA REASON into short (10 char) ERRCODE.
"""
import re
import logging
import traceback

# Table mapping REGEXP that matches a long-error to desired ERRCODE.
# ERRCODE max len = 10 char
ERRMAP = [ # (ERRCODE, MatchREGEX, Example), ...
    ('MISSFLD',
     re.compile(r"Missing FITS field "),
     'Missing FITS field \"DTPROPID\" in /home2/images/20161101/SO2016B-015.013'
    ),
    # 123456789_
    ('NOSCHED',
     re.compile(r"No propids in schedule slot: "),
     "No propids in schedule slot: Telescope=kp4m, Instrument=kosmos, Date=2099-09-28"
     ),
]

def code_err(reason):
    logging.debug('DBG: lookup code_err for: \"{}\"'.format(reason))
    for code, regex, example in ERRMAP:
        if regex.match(reason):
            return code[:10]
    logging.warning('Unknown TADA error: \"{}\"'.format(reason))
    logging.debug('TADA errorcoding Traceback:{}'.format(traceback.format_exc()))
    return 'TADAERR'

    

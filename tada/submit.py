"Dirt needed to submit a fits file to the archive for ingest"

import sys
import argparse
import logging
import pyfits
import os, os.path

from . import fits_utils as fu
from dataq import dqutils as du
from dataq import irods_utils as iu

class SubmitException (Exception):
    pass

class InvalidHeader (SubmitException):
    pass

def archive_ingest(fname):
    # register in irods
    # post metadata to archive port
    pass
    

def STUB_archive_ingest(fname):
    'Touch-point for archive ingest. Stub!!!'
    import random #!!! only needed for mockup
    import inspect

    logging.debug('Executing STUB: {}:STUB_archive_ingest()'.format(__file__))
    prop_fail = 0.60
    if random.random() <= prop_fail:  #!!! remove
        logging.debug(
            'Simulated FAILURE [p(Fail)={}] on STUB_archive_ingest({})'
            .format(prop_fail, fname))
        raise Exception(
            'Failed STUB_archive_ingest({}) due to cosmic ray (prob={}).'
            .format(fname, prop_fail))
    else:
        logging.debug(
            'Simulated SUCCESS [p(Fail)={}] on STUB_archive_ingest({})'
            .format(prop_fail, fname))
    return True

# Entry point to archive
#
# Problem: We need to change the filename to reflect naming
# standard. Ingest requires the new name be registered and to be on
# the local file system.  But if something goes wrong, we want the old
# name back. (reverse the side-effect of the name change) We will NOT
# reverse the side-effect of header modification.  We don't want to
# COPY (instead of MOVE) the file since it could be big.
def submit_to_archive(fname, qcfg):
    "Ingest a FITS file into archive, or stash it in Mitigation queue."
    irods_archive_dir = qcfg['submit']['archive_irods']
    archive_dir = qcfg['submit']['archive_dir']
    mo_fname = fu.molest(fname)
    new_fname = os.path.join(os.path.dirname(fname), mo_fname)
    os.rename(fname, new_fname)
    logging.debug('Modified header of fname: {}'.format(new_fname))

    successP, message = fu.valid_header(new_fname)
    if not successP:
        raise InvalidHeader('Invalid FITS header. {}'.format(message))

    iname = du.mirror_path(archive_dir, new_fname, irods_archive_dir)

    logging.debug('Registering {} to {} prior to ingest'
                  .format(new_fname, iname))
    iu.irods_reg(new_fname, iname)  # unregister with "irm -U"

    try:
        STUB_archive_ingest(new_fname)
    except:
        logging.debug('Unregister irods {} and undo the name change: {} => {}'
                      .format(iname, new_fname, fname))
        iu.irods_unreg(iname)
        os.rename(new_fname, fname)
        raise

    return new_fname

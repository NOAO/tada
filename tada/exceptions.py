import logging

from . import config
from . import audit
from . import utils as tut
from . import settings

auditor = audit.Auditor()

class NoPersonality(Exception):
    """We did not find expected YAML personality files 
in /var/tada/personalities/<INSTRUMENT>/*.yaml"""
    pass

class InvalidPersonality(Exception):
    "Personality file is invalid"
    pass


#################
class SubmitException(Exception):
    "Something went wrong with submit to archive"
    pass 

class InvalidHeader(SubmitException):
    "Exception when FITS header doesn't contains everything we need."
    pass

class InvalidFits(SubmitException):
    "FITS file failed CFITSIO verify test."
    pass

class ArchiveWebserviceProblem(SubmitException):
    "Exception on opening or reading Archive URL."
    pass

class CannotModifyHeader(SubmitException):
    "Exception when untrapped part of updating FITS header fails."
    pass

class HeaderMissingKeys(SubmitException):
    "Exception when FITS header doesn't contains everything we need."
    pass


#################
class IngestRejection(Exception):
    """File could not be ingested into archive. (We might not even attempt to
ingest if file is known to be invalid before hand)."""
    def __init__(self, md5sum, origfilename, errmsg, newhdr):
        self.md5sum = md5sum
        self.origfilename = origfilename
        self.errmsg = errmsg
        self.newhdr = newhdr # dict of new FITS metadata
        logging.debug('IngestRejection({}, {}, {}, {}); audited'
                      .format(self.md5sum, self.origfilename,
                              self.errmsg, self.newhdr))
        # Don't know why. Following does show in mars.
        #auditor.log_audit(md5sum,origfilename, False, '', errmsg, newhdr=newhdr)

    def __str__(self):
        return str('Rejected ingest of {}. REASON: {}'
                   .format(self.origfilename, self.errmsg))

class MarsWebserviceError(Exception):
    "Error connecting to MARS web service."
    pass

class BadPropid(Exception):
    "Required propid from header is invalid."
    pass
        

class InsufficientRawHeader(Exception):
    "FITS header does not contain minimal fields required to make additions."
    pass

class InsufficientArchiveHeader(Exception):
    "FITS header does not contain minimal fields required to put in archive."
    pass

class BadFieldContent(Exception):
    "A FITS header field value has bad content."
    pass

class NotInLut(Exception):
    "A used key was not found in an internal LookUp Table"
    pass

class IrodsContentException(Exception):
    "Irods contains something that prevents ingest"
    pass

class FailedIrodsCommand(Exception):
    "iRODS iCOMMAND failed"
    pass


class SuccessfulNonIngest(Exception):
    "We did not ingest. On purpose. (e.g. dry-run)"
    pass
    

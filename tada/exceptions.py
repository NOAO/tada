import logging
import traceback

from . import audit
from . import utils as tut


auditor = audit.Auditor()

class BaseTadaException(Exception):
    is_an_error_response = True
    filename      = '<NA>'
    error_message = '<NA>'
    error_code    = 'UNKTADAERR' 
    traceback     = None

    def get_subclass_name(self):
        return self.__class__.__name__
    
    def __init__(self, error_message, error_code=None):
        Exception.__init__(self)
        self.error_message = error_message
        self.error_code = error_code
        self.traceback = traceback.format_exc()
        logging.error('TADA-{}({}): {}'
                      .format(self.get_subclass_name(), error_code, error_message))
        
    def to_dict(self):
        return {'errorMessage': self.error_message,
                'errorCode': self.error_code  }

    
class NoPersonality(BaseTadaException):
    """We did not find expected YAML personality files 
in /var/tada/personalities/<INSTRUMENT>/*.yaml"""
    pass

class InvalidPersonality(BaseTadaException):
    "Personality file is invalid"
    pass


#################
class SubmitException(BaseTadaException):
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
class IngestRejection(BaseTadaException):
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
        ## log_audit(md5sum, origfname, success, archfile, reason, **kwargs)
        auditor.log_audit(md5sum,origfilename, False, '', errmsg, newhdr=newhdr)

    def __str__(self):
        return str('Rejected ingest of {}. REASON: {}'
                   .format(self.origfilename, self.errmsg))

class MarsWebserviceError(BaseTadaException):
    "Error connecting to MARS web service."
    pass

class BadPropid(BaseTadaException):
    "Required propid from header is invalid."
    pass
        

class InsufficientRawHeader(BaseTadaException):
    "FITS header does not contain minimal fields required to make additions."
    pass

class InsufficientArchiveHeader(BaseTadaException):
    "FITS header does not contain minimal fields required to put in archive."
    pass

class BadFieldContent(BaseTadaException):
    "A FITS header field value has bad content."
    pass

class NotInLut(BaseTadaException):
    "A used key was not found in an internal LookUp Table"
    pass

class SuccessfulNonIngest(BaseTadaException):
    "We did not ingest. On purpose. (e.g. dry-run)"
    pass
    
class BadHdrFunc(BaseTadaException):
    "Could not execute hdr function against a specific header"
    pass

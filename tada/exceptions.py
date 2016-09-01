import logging

from . import config
from . import audit
from . import tada_utils as tut

auditor = audit.Auditor()


class IngestRejection(Exception):
    """File could not be ingested into archive. (We might not even attempt to
ingest if file is known to be invalid before hand)."""
    #def __init__(self, localfits, srcpath, errmsg, newhdr):
    def __init__(self, md5sum, origfilename, errmsg, newhdr):
        self.errmsg = errmsg
        self.newhdr = newhdr # dict of new FITS metadata
        #print('DBG: IngestRejection; errmsg={}'.format(errmsg))
        auditor.log_audit(md5sum, origfilename, False, '', errmsg,
                          newhdr=newhdr)
        #logging.exception('IngestRejection: recorded with log_audit')
        tut.log_traceback()        

    def __str__(self):
        return str(self.errmsg)

class SubmitException(Exception):
    "Something went wrong with submit to archive"
    def __init__(self, errmsg):
        logging.error(errmsg)

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


class SuccessfulNonIngest(Exception):
    "We did not ingest. On purpose. (e.g. dry-run)"
    pass
    

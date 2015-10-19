
class SubmitException(Exception):
    "Something went wrong with submit to archive"
    pass

class InvalidHeader(SubmitException):
    "Exception when FITS header doesn't contains everything we need."
    pass

class HeaderMissingKeys(SubmitException):
    "Exception when FITS header doesn't contains everything we need."
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

class SubmitException(Exception):
    "Something went wrong with submit to archive"
    pass


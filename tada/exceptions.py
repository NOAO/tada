
class SubmitException(Exception):
    "Something went wrong with submit to archive"
    pass

class InvalidHeader(SubmitException):
    "Exception when FITS header doesn't contains everything we need."
    pass

class HeaderMissingKeys(SubmitException):
    "Exception when FITS header doesn't contains everything we need."
    pass

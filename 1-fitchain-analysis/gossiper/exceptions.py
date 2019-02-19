class FitchainError(Exception):
    """
    Base class for all py-evm errors.
    """
    pass


class ValidationError(FitchainError):
    """
    Raised when something does not pass a validation check.
    """
    pass


class DecryptionError(Exception):
    """
    Raised when a message could not be decrypted.
    """
    pass

class InvalidTransaction(Exception):
    """ Raised when an invalid transaction is received """
    pass

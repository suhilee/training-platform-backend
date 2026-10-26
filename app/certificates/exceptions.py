class RegistrationNotFoundError(Exception):
    pass


class AttendanceNotValidatedError(Exception):
    pass


class CertificateAlreadyIssuedError(Exception):
    pass


#for certifcate rendering
class CertificateNotFoundError(Exception):
    pass


class CertificateNotOwnedError(Exception):
    pass
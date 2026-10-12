class SessionNotFoundError(Exception):
    pass


class SessionCancelledError(Exception):
    pass


class IneligibleForSessionError(Exception):
    pass


class AlreadyRegisteredError(Exception):
    pass


class SessionFullError(Exception):
    pass


class SessionCompletedError(Exception):
    pass


class RegistrationClosedError(Exception):
    pass
# generic error, avoids revealing that a session exists outside their category
class SessionNotFoundOrIneligibleError(Exception):
    pass
# the session UUID does not exist.
class SessionNotFoundError(Exception):
    pass

# the session is open, running, or cancelled.
class SessionNotCompletedError(Exception):
    pass

# at least one submitted registration UUID does not belong
# to an attendance record for this session, or it was already validated.
class InvalidAttendanceSelectionError(Exception):
    pass

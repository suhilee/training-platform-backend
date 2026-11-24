# generic error, avoids revealing that a session exists outside their category
class SessionNotFoundOrIneligibleError(Exception):
    pass

class TrainingTypeNotFoundError(Exception):
    pass

class InstructorNotFoundError(Exception):
    """Raised when a session references an instructor that does not exist."""
    pass

class AgeCategoryNotFoundError(Exception):
    pass

# for session manager side error
class SessionNotFoundError(Exception):
    pass

# for session manager updating capacity with conflict
class CapacityBelowRegistrationCountError(Exception):
    pass

class TargetAgeCategoryHasRegistrationsError(Exception):
    pass

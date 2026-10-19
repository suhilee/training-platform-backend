# generic error, avoids revealing that a session exists outside their category
class SessionNotFoundOrIneligibleError(Exception):
    pass

class TrainingTypeNotFoundError(Exception):
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

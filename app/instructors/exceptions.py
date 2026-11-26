class InstructorNotFoundError(Exception):
    """Raised when an instructor does not exist."""


class InstructorEmailAlreadyExistsError(Exception):
    """Raised when an instructor email is already in use."""


class InstructorAssignedToSessionsError(Exception):
    """Raised when deleting an instructor still assigned to sessions."""


class InvalidInstructorPhotoTypeError(Exception):
    """Raised when an uploaded instructor photo has an unsupported type."""


class InstructorPhotoTooLargeError(Exception):
    """Raised when an uploaded instructor photo exceeds the size limit."""

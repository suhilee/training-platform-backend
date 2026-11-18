from uuid import UUID

from pydantic import BaseModel, Field


class AttendanceValidationRequest(BaseModel):
    registration_ids: list[UUID] = Field(min_length=1)

class AttendanceValidationResponse(BaseModel):
    validated_count: int

class SessionAttendeeResponse(BaseModel):
    registration_id: UUID
    first_name: str
    last_name: str
    has_attended: bool
    attendance_validated: bool
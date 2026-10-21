from uuid import UUID

from pydantic import BaseModel, Field


class AttendanceValidationRequest(BaseModel):
    registration_ids: list[UUID] = Field(min_length=1)

class AttendanceValidationResponse(BaseModel):
    validated_count: int

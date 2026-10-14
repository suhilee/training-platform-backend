from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel


class RegistrationResponse(BaseModel):
    id: UUID
    session_id: UUID
    registered_at: datetime


class SessionListItemResponse(BaseModel):
    id: UUID
    title: str
    description: str
    date: date
    start_time: time
    duration_minutes: int
    max_capacity: int
    registered_count: int
    instructor_name: str
    is_cancelled: bool
    status: str

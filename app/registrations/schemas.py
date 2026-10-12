from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RegistrationResponse(BaseModel):
    id: UUID
    session_id: UUID
    registered_at: datetime
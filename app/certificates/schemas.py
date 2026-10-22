from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
    id: UUID
    registration_id: UUID
    issued_at: datetime
    validated_by: UUID

    model_config = ConfigDict(from_attributes=True)

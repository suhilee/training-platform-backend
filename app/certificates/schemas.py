from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
    id: UUID
    registration_id: UUID
    issued_at: datetime
    validated_by: UUID

    model_config = ConfigDict(from_attributes=True)

#for certificate rendering
class CertificateDataResponse(BaseModel):
    registration_id: UUID
    certificate_id: UUID
    participant_first_name: str
    participant_last_name: str
    session_title: str
    session_date: date
    issued_at: datetime
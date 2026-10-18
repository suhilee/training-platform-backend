from uuid import UUID

from pydantic import BaseModel


class TrainingTypeListItemResponse(BaseModel):
    id: UUID
    training_code: str
    name: str
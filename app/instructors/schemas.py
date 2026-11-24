from uuid import UUID

from pydantic import BaseModel


class InstructorListItemResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str

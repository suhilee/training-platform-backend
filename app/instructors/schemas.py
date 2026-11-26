from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class InstructorListItemResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    bio: str | None
    photo_url: str | None
    is_featured: bool


class InstructorCreateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    bio: str | None = Field(default=None, max_length=2_000)
    is_featured: bool = False


class InstructorUpdateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    bio: str | None = Field(default=None, max_length=2_000)
    is_featured: bool


class PublicInstructorListItemResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    bio: str | None
    photo_url: str

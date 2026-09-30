from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone_number: str = Field(min_length=1, max_length=30)
    date_of_birth: date
    wilaya: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)

class RegisterResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone_number: str
    date_of_birth: date
    age_category_id: int
    wilaya: str
    role: UserRole
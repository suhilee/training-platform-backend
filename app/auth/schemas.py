from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone_number: str = Field(min_length=1, max_length=30)
    date_of_birth: date
    wilaya: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)

class RegisterResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    date_of_birth: date
    age_category_id: int
    wilaya: str
    role: UserRole

class CurrentUserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    date_of_birth: date
    age_category_id: int
    wilaya: str
    role: UserRole

class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None)
    phone_number: str | None = Field(default=None, min_length=1, max_length=30)
    wilaya: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = Field(default=None)

class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

class PasswordResetRequestRequest(BaseModel):
    email: EmailStr

class PasswordResetRequestResponse(BaseModel):
    message: str
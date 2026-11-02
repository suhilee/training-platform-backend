import pytest
from pydantic import ValidationError

from app.auth.schemas import (
    ChangePasswordRequest,
    PasswordResetRequest,
    RegisterRequest,
)


def register_data(password: str) -> dict:
    return {
        "first_name": "Souhil",
        "last_name": "MANDI",
        "email": "password-validation@example.com",
        "phone_number": "0550123456",
        "date_of_birth": "2000-01-01",
        "wilaya": "Alger",
        "password": password,
    }


@pytest.mark.parametrize(
    "password",
    [
        "strongpassword123",
        "STRONGPASSWORD123",
        "StrongPassword",
        "Str1",
    ],
)
def test_register_rejects_weak_passwords(password: str) -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(**register_data(password))


def test_register_accepts_strong_password() -> None:
    request = RegisterRequest(**register_data("StrongPassword123"))

    assert request.password == "StrongPassword123"


def test_change_password_rejects_weak_password() -> None:
    with pytest.raises(ValidationError):
        ChangePasswordRequest(
            current_password="OldPassword123",
            new_password="weakpass123",
        )


def test_change_password_accepts_strong_password() -> None:
    request = ChangePasswordRequest(
        current_password="OldPassword123",
        new_password="StrongPassword123",
    )

    assert request.new_password == "StrongPassword123"


def test_password_reset_rejects_weak_password() -> None:
    with pytest.raises(ValidationError):
        PasswordResetRequest(
            token="reset-token",
            new_password="weakpass123",
        )


def test_password_reset_accepts_strong_password() -> None:
    request = PasswordResetRequest(
        token="reset-token",
        new_password="StrongPassword123",
    )

    assert request.new_password == "StrongPassword123"
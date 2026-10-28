from datetime import datetime, timedelta, timezone, date

import pytest
from sqlalchemy.orm import Session

from app.auth.exceptions import InvalidPasswordResetTokenError
from app.auth.password import hash_password, verify_password
from app.auth.service import (
    create_password_reset_token,
    hash_reset_token,
    reset_password,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.age_category import AgeCategory
from app.models.user import User


def create_age_category(db: Session) -> AgeCategory:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )
    
    db.add(age_category)
    db.commit()
    db.refresh(age_category)
    return age_category


def create_user(db: Session, email: str) -> User:
    age_category = create_age_category(db)

    user = User(
        first_name="Test",
        last_name="User",
        email=email,
        phone_number="0550000000",
        date_of_birth=date(2000,1,1),
        wilaya="Alger",
        password_hash=hash_password("OldPassword123"),
        age_category_id=age_category.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_reset_password_updates_password_and_marks_token_used(
    db_session: Session,
) -> None:
    user = create_user(db_session, "reset-valid@example.com")

    create_password_reset_token(db_session, user.email)

    token = db_session.query(PasswordResetToken).one()
    token.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db_session.commit()

    raw_token = "raw-test-token"
    token.token_hash = hash_reset_token(raw_token)
    db_session.commit()

    reset_password(db_session, raw_token, "NewPassword123")

    db_session.refresh(user)
    db_session.refresh(token)

    assert verify_password("NewPassword123", user.password_hash)
    assert token.used_at is not None


def test_reset_password_rejects_unknown_token(
    db_session: Session,
) -> None:
    with pytest.raises(InvalidPasswordResetTokenError):
        reset_password(db_session, "unknown-token", "NewPassword123")


def test_reset_password_rejects_used_token(
    db_session: Session,
) -> None:
    user = create_user(db_session, "reset-used@example.com")

    create_password_reset_token(db_session, user.email)

    token = db_session.query(PasswordResetToken).one()
    token.token_hash = hash_reset_token("used-token")
    token.used_at = datetime.now(timezone.utc)
    db_session.commit()

    with pytest.raises(InvalidPasswordResetTokenError):
        reset_password(db_session, "used-token", "NewPassword123")


def test_reset_password_rejects_expired_token(
    db_session: Session,
) -> None:
    user = create_user(db_session, "reset-expired@example.com")

    create_password_reset_token(db_session, user.email)

    token = db_session.query(PasswordResetToken).one()
    token.token_hash = hash_reset_token("expired-token")
    token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    with pytest.raises(InvalidPasswordResetTokenError):
        reset_password(db_session, "expired-token", "NewPassword123")
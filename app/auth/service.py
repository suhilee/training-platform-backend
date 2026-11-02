from uuid import UUID

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.age_category import AgeCategory

from app.models.password_reset_token import PasswordResetToken
from app.notifications.email import ConsoleEmailSender, EmailMessage
from app.auth.exceptions import (
    InvalidPasswordResetTokenError,
    InvalidVerificationTokenError,
)

from app.auth.schemas import RegisterRequest
from app.models.user import User
from app.models.email_verification_token import EmailVerificationToken

from app.auth.password import hash_password

from sqlalchemy.exc import IntegrityError


PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 30
EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = 24
EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS = 60

def hash_email_verification_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.execute(statement).scalar_one_or_none()

def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)

def send_verification_email(db: Session, user: User) -> None:
    raw_token = secrets.token_urlsafe(32)

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_email_verification_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
    )

    db.add(verification_token)
    db.commit()

    verification_link = (
        f"{settings.frontend_base_url}/verify-email"
        f"?token={raw_token}"
    )

    email_sender = ConsoleEmailSender()
    email_sender.send(
        EmailMessage(
            to_email=user.email,
            subject="Verify your email address",
            body=(
                f"Hello {user.first_name},\n\n"
                "Please verify your email address by opening "
                "the following link:\n"
                f"{verification_link}\n\n"
                "This link expires in 24 hours."
            ),
        )
    )

def resend_verification_email(db: Session, email: str) -> None:
    user = get_user_by_email(db, email)

    if user is None or user.email_verified:
        return

    latest_token = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.user_id == user.id,
        )
        .order_by(EmailVerificationToken.created_at.desc())
        .first()
    )

    now = datetime.now(timezone.utc)

    if latest_token is not None:
        cooldown_end = latest_token.created_at + timedelta(
            seconds=EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS,
        )

        if now < cooldown_end:
            return

    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used_at.is_(None),
    ).update(
        {"used_at": now},
        synchronize_session=False,
    )

    db.commit()

    send_verification_email(db, user)

def create_participant(db: Session, registration: RegisterRequest, age_category: AgeCategory) -> User:
    user = User(
    first_name=registration.first_name,
    last_name=registration.last_name,
    email=registration.email,
    phone_number=registration.phone_number,
    date_of_birth=registration.date_of_birth,
    age_category_id=age_category.id,
    wilaya=registration.wilaya,
    password_hash=hash_password(registration.password),
    email_verified=False,
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(user)

    send_verification_email(db, user)

    return user

def hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def create_password_reset_token(
    db: Session,
    email: str,
) -> None:
    user = get_user_by_email(db, email)

    if user is None:
        return

    raw_token = secrets.token_urlsafe(32)

    password_reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )

    db.add(password_reset_token)
    db.commit()

    reset_link = (
        f"{settings.frontend_base_url}/reset-password"
        f"?token={raw_token}"
    )

    email_sender = ConsoleEmailSender()
    email_sender.send(
        EmailMessage(
            to_email=user.email,
            subject="Reset your password",
            body=(
                "Use the following link to reset your password:\n"
                f"{reset_link}\n\n"
                "This link expires in 30 minutes."
            ),
        )
    )

def reset_password(
        db: Session,
        raw_token: str,
        new_password: str,
) -> None:
    token_hash = hash_reset_token(raw_token)

    password_reset_token = db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
    ).scalar_one_or_none()

    if password_reset_token is None:
        raise InvalidPasswordResetTokenError

    if password_reset_token.used_at is not None:
        raise InvalidPasswordResetTokenError

    if password_reset_token.expires_at <= datetime.now(timezone.utc):
        raise InvalidPasswordResetTokenError

    user = db.get(User, password_reset_token.user_id)

    if user is None:
        raise InvalidPasswordResetTokenError

    user.password_hash = hash_password(new_password)
    password_reset_token.used_at = datetime.now(timezone.utc)

    db.commit()

def verify_email(db: Session, raw_token: str) -> None:
    token_hash = hash_email_verification_token(raw_token)

    verification_token = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.token_hash == token_hash,
        )
        .first()
    )

    if verification_token is None:
        raise InvalidVerificationTokenError()

    now = datetime.now(timezone.utc)

    if verification_token.used_at is not None:
        raise InvalidVerificationTokenError()

    if verification_token.expires_at <= now:
        raise InvalidVerificationTokenError()

    user = db.query(User).filter(User.id == verification_token.user_id).first()

    if user is None:
        raise InvalidVerificationTokenError()

    if user.email_verified:
        raise InvalidVerificationTokenError()

    user.email_verified = True
    verification_token.used_at = now

    db.commit()

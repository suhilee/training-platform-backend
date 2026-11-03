from datetime import date
from unittest.mock import patch

from sqlalchemy.orm import Session

from app.auth.schemas import RegisterRequest
from app.auth.service import (
    create_participant,
    create_password_reset_token,
    resend_verification_email,
)
from app.models.age_category import AgeCategory
from app.models.email_verification_token import EmailVerificationToken
from app.models.user import User
from app.notifications.email import ConsoleEmailSender


def test_resend_verification_email_failure_does_not_unverify_user(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        code="AD",
        min_age=18,
        max_age=59,
    )

    db_session.add(age_category)
    db_session.commit()
    db_session.refresh(age_category)

    registration = RegisterRequest(
        first_name="Souhil",
        last_name="Test",
        email="resend-email-failure@example.com",
        phone_number="0550000000",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password="StrongPassword123",
    )

    create_participant(
        db=db_session,
        registration=registration,
        age_category=age_category,
    )

    with patch.object(
        ConsoleEmailSender,
        "send",
        side_effect=RuntimeError("Email provider unavailable"),
    ):
        resend_verification_email(
            db=db_session,
            email=registration.email,
        )

    user = (
        db_session.query(User)
        .filter(User.email == registration.email)
        .one()
    )

    token = (
        db_session.query(EmailVerificationToken)
        .filter(EmailVerificationToken.user_id == user.id)
        .one()
    )

    assert user.email_verified is False
    assert token.used_at is None
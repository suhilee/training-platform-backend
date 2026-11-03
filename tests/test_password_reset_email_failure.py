from datetime import date
from unittest.mock import patch

from sqlalchemy.orm import Session

from app.auth.schemas import RegisterRequest
from app.auth.service import create_participant, create_password_reset_token
from app.models.age_category import AgeCategory
from app.models.password_reset_token import PasswordResetToken
from app.notifications.email import ConsoleEmailSender

from app.models.user import User

def test_password_reset_token_remains_committed_when_email_delivery_fails(
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
        email="reset-email-failure@example.com",
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
        create_password_reset_token(
            db=db_session,
            email=registration.email,
        )

    token = (
        db_session.query(PasswordResetToken)
        .join(User, User.id == PasswordResetToken.user_id)
        .filter(User.email == registration.email)
        .one()
    )

    assert token.used_at is None
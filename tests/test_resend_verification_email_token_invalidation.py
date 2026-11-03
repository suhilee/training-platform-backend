from datetime import date, timedelta, timezone, datetime
from unittest.mock import patch

from sqlalchemy.orm import Session

from app.auth.schemas import RegisterRequest
from app.auth.service import (
    create_participant,
    resend_verification_email,
)
from app.models.age_category import AgeCategory
from app.models.email_verification_token import EmailVerificationToken
from app.models.user import User
from app.notifications.email import ConsoleEmailSender


def test_resend_verification_email_invalidates_previous_unused_token(
    db_session: Session,
    monkeypatch,
):
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
        email="resend-invalidation@example.com",
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

    user = (
        db_session.query(User)
        .filter(User.email == registration.email)
        .one()
    )

    original_token = (
        db_session.query(EmailVerificationToken)
        .filter(EmailVerificationToken.user_id == user.id)
        .one()
    )

    # Make the original token old enough to pass the 60-second cooldown.
    original_token.created_at = (
        datetime.now(timezone.utc) - timedelta(minutes=2)
    )
    db_session.commit()

    with patch.object(ConsoleEmailSender, "send"):
        resend_verification_email(
            db=db_session,
            email=registration.email,
        )

    tokens = (
        db_session.query(EmailVerificationToken)
        .filter(EmailVerificationToken.user_id == user.id)
        .all()
    )

    assert len(tokens) == 2

    original_token_after_resend = next(
        token
        for token in tokens
        if token.id == original_token.id
    )

    new_token = next(
        token
        for token in tokens
        if token.id != original_token.id
    )

    assert original_token_after_resend.used_at is not None
    assert new_token.used_at is None
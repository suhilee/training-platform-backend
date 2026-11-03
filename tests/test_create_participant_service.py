from datetime import date

from unittest.mock import patch

from sqlalchemy.orm import Session

from app.auth.service import create_participant
from app.auth.schemas import RegisterRequest
from app.models.age_category import AgeCategory
from app.models.user import User
from app.notifications.email import ConsoleEmailSender


def test_create_participant_commits_user_when_email_delivery_fails(
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
        email="email-failure@example.com",
        phone_number="0550000000",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password="StrongPassword123",
    )

    with patch.object(
        ConsoleEmailSender,
        "send",
        side_effect=RuntimeError("Email provider unavailable"),
    ):
        user = create_participant(
            db=db_session,
            registration=registration,
            age_category=age_category,
        )

    assert user.email_verified is False

    saved_user = (
        db_session.query(User)
        .filter(User.email == registration.email)
        .one()
    )

    assert saved_user.id == user.id
    assert saved_user.email_verified is False
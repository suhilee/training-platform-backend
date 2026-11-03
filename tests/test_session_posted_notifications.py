from datetime import date, time
from unittest.mock import patch

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.age_category import AgeCategory
from app.models.session import Session as TrainingSession
from app.models.session_target_category import SessionTargetCategory
from app.models.training_type import TrainingType
from app.models.user import User, UserRole
from app.notifications.email import ConsoleEmailSender
from app.sessions.notifications import send_session_posted_emails


def create_session_posted_fixture(db_session: Session) -> TrainingSession:
    target_age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    other_age_category = AgeCategory(
        id=2,
        code="SR",
        min_age=60,
        max_age=99,
    )

    first_eligible_user = User(
        first_name="First",
        last_name="Eligible",
        email="first-posted@example.com",
        phone_number="0550000001",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=target_age_category.id,
        role=UserRole.PARTICIPANT,
    )

    second_eligible_user = User(
        first_name="Second",
        last_name="Eligible",
        email="second-posted@example.com",
        phone_number="0550000002",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=target_age_category.id,
        role=UserRole.PARTICIPANT,
    )

    ineligible_user = User(
        first_name="Ineligible",
        last_name="User",
        email="ineligible-posted@example.com",
        phone_number="0550000003",
        date_of_birth=date(1950, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=other_age_category.id,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="POSTED-TEST",
        name="Session Posted Test Training",
    )

    training_session = TrainingSession(
        training_type=training_type,
        title="Python Fundamentals",
        description="A newly posted training session.",
        date=date(2030, 1, 15),
        start_time=time(10, 0),
        duration_minutes=90,
        max_capacity=100,
        zoom_url="https://zoom.example.com/posted-session",
        instructor_name="Test Instructor",
    )

    db_session.add_all(
        [
            target_age_category,
            other_age_category,
            first_eligible_user,
            second_eligible_user,
            ineligible_user,
            training_type,
            training_session,
        ]
    )
    db_session.flush()

    training_session.target_categories.append(
        SessionTargetCategory(
            age_category_id=target_age_category.id,
        )
    )

    db_session.commit()
    db_session.refresh(training_session)

    return training_session


def test_sends_one_email_per_user_in_target_age_categories(
    db_session: Session,
) -> None:
    training_session = create_session_posted_fixture(db_session)

    with patch.object(ConsoleEmailSender, "send") as send_mock:
        send_session_posted_emails(
            db=db_session,
            training_session=training_session,
        )

    assert send_mock.call_count == 2

    recipients = {
        call.args[0].to_email
        for call in send_mock.call_args_list
    }

    assert recipients == {
        "first-posted@example.com",
        "second-posted@example.com",
    }


def test_posted_email_contains_session_details_and_link(
    db_session: Session,
) -> None:
    training_session = create_session_posted_fixture(db_session)

    with patch.object(ConsoleEmailSender, "send") as send_mock:
        send_session_posted_emails(
            db=db_session,
            training_session=training_session,
        )

    assert send_mock.call_count == 2

    messages = [
        call.args[0]
        for call in send_mock.call_args_list
    ]

    expected_session_url = (
        f"{settings.frontend_base_url}/sessions/{training_session.id}"
    )

    for message in messages:
        assert message.subject == (
            "New training session available: Python Fundamentals"
        )
        assert "Python Fundamentals" in message.body
        assert "2030-01-15" in message.body
        assert "10:00:00" in message.body
        assert expected_session_url in message.body
        assert "one hour before it starts" in message.body


def test_posted_email_does_not_contain_zoom_url(
    db_session: Session,
) -> None:
    training_session = create_session_posted_fixture(db_session)

    with patch.object(ConsoleEmailSender, "send") as send_mock:
        send_session_posted_emails(
            db=db_session,
            training_session=training_session,
        )

    messages = [
        call.args[0]
        for call in send_mock.call_args_list
    ]

    for message in messages:
        assert training_session.zoom_url not in message.body


def test_posted_emails_continue_after_delivery_failure(
        db_session: Session,
) -> None:
    training_session = create_session_posted_fixture(db_session)

    with patch.object(
        ConsoleEmailSender,
        "send",
        side_effect=[
            RuntimeError("Email provider unavailable"),
            None,
        ],
    ) as send_mock:
        send_session_posted_emails(
            db=db_session,
            training_session= training_session,
        )

    assert send_mock.call_count == 2

    recipients = {
        call.args[0].to_email
        for call in send_mock.call_args_list
    }

    assert recipients == {
        "first-posted@example.com",
        "second-posted@example.com",
    }
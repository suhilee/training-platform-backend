from datetime import date, time
from unittest.mock import patch

from sqlalchemy.orm import Session

from app.models.age_category import AgeCategory
from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.user import User, UserRole
from app.notifications.email import ConsoleEmailSender
from app.sessions.notifications import send_session_cancellation_emails


def create_cancellation_fixture(db_session: Session) -> TrainingSession:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    first_participant = User(
        first_name="First",
        last_name="Participant",
        email="first-cancellation@example.com",
        phone_number="0550000001",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.PARTICIPANT,
    )

    second_participant = User(
        first_name="Second",
        last_name="Participant",
        email="second-cancellation@example.com",
        phone_number="0550000002",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.PARTICIPANT,
    )

    unregistered_user = User(
        first_name="Unregistered",
        last_name="User",
        email="unregistered@example.com",
        phone_number="0550000003",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="CANCELLATION-TEST",
        name="Cancellation Test Training",
    )

    training_session = TrainingSession(
        training_type=training_type,
        title="Python Fundamentals",
        description="A session used to test cancellation emails.",
        date=date(2030, 1, 15),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/cancellation",
        instructor_name="Test Instructor",
    )

    db_session.add_all(
        [
            age_category,
            first_participant,
            second_participant,
            unregistered_user,
            training_type,
            training_session,
        ]
    )
    db_session.flush()

    first_registration = Registration(
        user_id=first_participant.id,
        session_id=training_session.id,
    )

    second_registration = Registration(
        user_id=second_participant.id,
        session_id=training_session.id,
    )

    db_session.add_all(
        [
            first_registration,
            second_registration,
        ]
    )
    db_session.commit()
    db_session.refresh(training_session)

    return training_session


def test_sends_one_cancellation_email_per_registered_participant(
    db_session: Session,
) -> None:
    training_session = create_cancellation_fixture(db_session)

    with patch.object(ConsoleEmailSender, "send") as send_mock:
        send_session_cancellation_emails(
            db=db_session,
            training_session=training_session,
        )

    assert send_mock.call_count == 2

    recipients = {
        call.args[0].to_email
        for call in send_mock.call_args_list
    }

    assert recipients == {
        "first-cancellation@example.com",
        "second-cancellation@example.com",
    }


def test_cancellation_email_contains_session_details(
    db_session: Session,
) -> None:
    training_session = create_cancellation_fixture(db_session)

    with patch.object(ConsoleEmailSender, "send") as send_mock:
        send_session_cancellation_emails(
            db=db_session,
            training_session=training_session,
        )

    assert send_mock.call_count == 2

    
    messages = [
        call.args[0]
        for call in send_mock.call_args_list
    ]

    for message in messages:
        assert message.subject == (
            "Session cancelled: Python Fundamentals"
        )
        assert "Python Fundamentals" in message.body
        assert "2030-01-15" in message.body
        assert "10:00:00" in message.body
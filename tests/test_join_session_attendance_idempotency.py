from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from sqlalchemy.orm import Session

from app.auth.schemas import RegisterRequest
from app.auth.service import create_participant
from app.models.age_category import AgeCategory
from app.models.attendance import Attendance
from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.session_target_category import SessionTargetCategory
from app.models.training_type import TrainingType
from app.models.user import User
from app.notifications.email import ConsoleEmailSender
from app.registrations.service import (
    join_session,
    register_for_session,
)


def test_join_session_does_not_create_duplicate_attendance(
    db_session: Session,
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
        email="join-idempotency@example.com",
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

    training_type = TrainingType(
        training_code= "c1",
        name="Test Training Type",
    )

    db_session.add(training_type)
    db_session.commit()
    db_session.refresh(training_type)

    training_session = TrainingSession(
        training_id=training_type.id,
        title="Join idempotency session",
        description="Test session",
        date=date.today(),
        start_time=time(23, 0),
        duration_minutes=60,
        max_capacity=10,
        registered_count=0,
        instructor_name="instruct",
        zoom_url="https://zoom.example.com/test",
        is_cancelled=False,
    )

    db_session.add(training_session)
    db_session.commit()
    db_session.refresh(training_session)

    session_target_category = SessionTargetCategory(
        session=training_session,
        age_category_id=age_category.id,
    )

    db_session.add(session_target_category)
    db_session.commit()

    register_for_session(
        db=db_session,
        current_user=user,
        session_id=training_session.id,
    )

    now = datetime.now()

    training_session.date = now.date()
    training_session.start_time = (
        now + timedelta(minutes=30)
    ).time()
    training_session.duration_minutes = 60

    db_session.commit()

    with patch.object(ConsoleEmailSender, "send"):
        join_session(
            db=db_session,
            current_user=user,
            session_id=training_session.id,
        )

        join_session(
            db=db_session,
            current_user=user,
            session_id=training_session.id,
        )

    registration_record = (
        db_session.query(Registration)
        .filter(
            Registration.user_id == user.id,
            Registration.session_id == training_session.id,
        )
        .one()
    )

    attendance_count = (
        db_session.query(Attendance)
        .filter(
            Attendance.registration_id == registration_record.id,
        )
        .count()
    )

    assert attendance_count == 1
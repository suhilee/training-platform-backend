from uuid import uuid4
from datetime import date, time, timedelta, datetime
import pytest
from sqlalchemy.orm import Session

from app.attendance.service import validate_attendances
from app.models.attendance import Attendance
from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.user import User, UserRole
from app.models.age_category import AgeCategory
from app.models.certificate import Certificate
from app.attendance.exceptions import(
    InvalidAttendanceSelectionError,
    SessionNotCompletedError,
    SessionNotFoundError,
)

def test_validate_attendances_marks_selected_attendances_as_validated(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        id=1,
        code="C1",
        min_age=7,
        max_age=10,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="manager@example.com",
        phone_number="0550000000",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    first_participant = User(
        first_name="First",
        last_name="Participant",
        email="first@example.com",
        phone_number="0550000001",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    second_participant = User(
        first_name="Second",
        last_name="Participant",
        email="second@example.com",
        phone_number="0550000002",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="ATTENDANCE-TEST",
        name="Attendance Test Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed session",
        description="A completed session for validation testing.",
        date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/meeting",
        instructor_name="Test Instructor",
    )

    db_session.add_all(
        [
            age_category,
            manager,
            first_participant,
            second_participant,
            training_type,
            completed_session,
        ]
    )
    db_session.commit()

    first_registration = Registration(
        user_id=first_participant.id,
        session_id=completed_session.id,
    )

    second_registration = Registration(
        user_id=second_participant.id,
        session_id=completed_session.id,
    )

    db_session.add_all([first_registration, second_registration])
    db_session.commit()

    first_attendance = Attendance(
        registration_id=first_registration.id,
    )

    second_attendance = Attendance(
        registration_id=second_registration.id,
    )

    db_session.add_all([first_attendance, second_attendance])
    db_session.commit()

    validated_count = validate_attendances(
        db=db_session,
        session_id=completed_session.id,
        registration_ids=[
            first_registration.id,
            second_registration.id,
        ],
        current_manager=manager,
    )

    db_session.refresh(first_attendance)
    db_session.refresh(second_attendance)

    certificates = (
        db_session.query(Certificate)
        .filter(
            Certificate.registration_id.in_(
                [
                    first_registration.id,
                    second_registration.id,
                ]
            )
        )
        .all()
    )

    assert len(certificates) == 2

    certificate_registration_ids = {
        certificate.registration_id
        for certificate in certificates
    }

    assert certificate_registration_ids == {
        first_registration.id,
        second_registration.id,
    }
    
    assert validated_count == 2

    assert first_attendance.validated_at is not None
    assert first_attendance.validated_by == manager.id

    assert second_attendance.validated_at is not None
    assert second_attendance.validated_by == manager.id

def test_validate_attendances_rejects_registration_from_another_session(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        id=1,
        code="C1",
        min_age=7,
        max_age=10,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="manager-cross-session@example.com",
        phone_number="0550000010",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.SESSION_MANAGER,
    )

    participant = User(
        first_name="Participant",
        last_name="User",
        email="participant-cross-session@example.com",
        phone_number="0550000011",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="CROSS-SESSION-TEST",
        name="Cross Session Test Training",
    )

    target_session = TrainingSession(
        training_type=training_type,
        title="Target completed session",
        description="The session named in the validation request.",
        date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/target",
        instructor_name="Test Instructor",
    )

    other_session = TrainingSession(
        training_type=training_type,
        title="Other completed session",
        description="The session that owns the invalid registration.",
        date=date.today() - timedelta(days=2),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/other",
        instructor_name="Test Instructor",
    )

    db_session.add_all(
        [
            age_category,
            manager,
            participant,
            training_type,
            target_session,
            other_session,
        ]
    )
    db_session.commit()

    other_registration = Registration(
        user_id=participant.id,
        session_id=other_session.id,
    )

    db_session.add(other_registration)
    db_session.commit()

    other_attendance = Attendance(
        registration_id=other_registration.id,
    )

    db_session.add(other_attendance)
    db_session.commit()

    with pytest.raises(InvalidAttendanceSelectionError):
        validate_attendances(
            db=db_session,
            session_id=target_session.id,
            registration_ids=[other_registration.id],
            current_manager=manager,
        )

def test_validate_attendances_rejects_session_that_is_not_completed(
    db_session: Session,
) -> None:
    training_type = TrainingType(
        training_code="NOT-COMPLETED-TEST",
        name="Not Completed Test Training",
    )

    unfinished_session = TrainingSession(
        training_type=training_type,
        title="Unfinished session",
        description="A session that has not ended yet.",
        date=date.today(),
        start_time=datetime.now().time(),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/unfinished",
        instructor_name="Test Instructor",
    )

    db_session.add_all([training_type, unfinished_session])
    db_session.commit()

    with pytest.raises(SessionNotCompletedError):
        validate_attendances(
            db=db_session,
            session_id=unfinished_session.id,
            registration_ids=[],
            current_manager=None,
        )

def test_validate_attendances_rejects_missing_session(
    db_session: Session,
) -> None:
    with pytest.raises(SessionNotFoundError):
        validate_attendances(
            db=db_session,
            session_id=uuid4(),
            registration_ids=[],
            current_manager=None,
        )

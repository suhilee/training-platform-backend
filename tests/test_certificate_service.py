import pytest

from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.certificates.service import issue_certificate
from app.models.age_category import AgeCategory
from app.models.attendance import Attendance
from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.user import User, UserRole
from app.models.certificate import Certificate

from app.certificates.exceptions import (
    AttendanceNotValidatedError,
    CertificateAlreadyIssuedError,
)

def test_issue_certificate_for_validated_attendance(
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
        email="manager-certificate@example.com",
        phone_number="0550000100",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.SESSION_MANAGER,
    )

    participant = User(
        first_name="Participant",
        last_name="User",
        email="participant-certificate@example.com",
        phone_number="0550000101",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="CERTIFICATE-TEST",
        name="Certificate Test Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed certificate session",
        description="A completed session for certificate testing.",
        date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/certificate-test",
        instructor_name="Test Instructor",
    )

    db_session.add_all(
        [
            age_category,
            manager,
            participant,
            training_type,
            completed_session,
        ]
    )
    db_session.commit()

    registration = Registration(
        user_id=participant.id,
        session_id=completed_session.id,
    )

    db_session.add(registration)
    db_session.commit()

    attendance = Attendance(
        registration_id=registration.id,
        validated_at=datetime.now(),
        validated_by=manager.id,
    )

    db_session.add(attendance)
    db_session.commit()

    certificate = issue_certificate(
        db=db_session,
        registration_id=registration.id,
        current_manager=manager,
    )

    assert certificate.id is not None
    assert certificate.registration_id == registration.id
    assert certificate.validated_by == manager.id
    assert certificate.issued_at is not None

def test_issue_certificate_rejects_unvalidated_attendance(
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
        email="manager-unvalidated@example.com",
        phone_number="0550000200",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.SESSION_MANAGER,
    )

    participant = User(
        first_name="Participant",
        last_name="User",
        email="participant-unvalidated@example.com",
        phone_number="0550000201",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="UNVALIDATED-CERTIFICATE-TEST",
        name="Unvalidated Certificate Test Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed session with unvalidated attendance",
        description="A completed session for certificate rejection testing.",
        date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/unvalidated-certificate-test",
        instructor_name="Test Instructor",
    )

    db_session.add_all(
        [
            age_category,
            manager,
            participant,
            training_type,
            completed_session,
        ]
    )
    db_session.commit()

    registration = Registration(
        user_id=participant.id,
        session_id=completed_session.id,
    )
    db_session.add(registration)
    db_session.commit()

    attendance = Attendance(
        registration_id=registration.id,
    )
    db_session.add(attendance)
    db_session.commit()

    with pytest.raises(AttendanceNotValidatedError):
        issue_certificate(
            db=db_session,
            registration_id=registration.id,
            current_manager=manager,
        )

def test_issue_certificate_rejects_duplicate_certificate(
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
        email="manager-duplicate@example.com",
        phone_number="0550000300",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.SESSION_MANAGER,
    )

    participant = User(
        first_name="Participant",
        last_name="User",
        email="participant-duplicate@example.com",
        phone_number="0550000301",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="DUPLICATE-CERTIFICATE-TEST",
        name="Duplicate Certificate Test Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed session with a certificate",
        description="A completed session for duplicate certificate testing.",
        date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/duplicate-certificate-test",
        instructor_name="Test Instructor",
    )

    db_session.add_all(
        [
            age_category,
            manager,
            participant,
            training_type,
            completed_session,
        ]
    )
    db_session.commit()

    registration = Registration(
        user_id=participant.id,
        session_id=completed_session.id,
    )
    db_session.add(registration)
    db_session.commit()

    attendance = Attendance(
        registration_id=registration.id,
        validated_at=datetime.now(),
        validated_by=manager.id,
    )
    existing_certificate = Certificate(
        registration_id=registration.id,
        validated_by=manager.id,
    )

    db_session.add_all([attendance, existing_certificate])
    db_session.commit()

    with pytest.raises(CertificateAlreadyIssuedError):
        issue_certificate(
            db=db_session,
            registration_id=registration.id,
            current_manager=manager,
        )
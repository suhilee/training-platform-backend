from datetime import date, time, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.certificates.exceptions import (
    CertificateNotOwnedError,
    RegistrationNotFoundError,
    CertificateNotFoundError,
)

from app.certificates.service import get_certificate_data
from app.models.age_category import AgeCategory
from app.models.certificate import Certificate
from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.user import User, UserRole


def test_get_certificate_data_rejects_certificate_not_owned_by_current_user(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    owner = User(
        first_name="Owner",
        last_name="Participant",
        email="certificate-owner@example.com",
        phone_number="0550000020",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    attacker = User(
        first_name="Attacker",
        last_name="Participant",
        email="certificate-attacker@example.com",
        phone_number="0550000021",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="certificate-manager@example.com",
        phone_number="0550000022",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    training_type = TrainingType(
        training_code="CERTIFICATE-OWNERSHIP-TEST",
        name="Certificate Ownership Test Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed session",
        description="A completed session for certificate ownership testing.",
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
            owner,
            attacker,
            manager,
            training_type,
            completed_session,
        ]
    )
    db_session.flush()

    owner_registration = Registration(
        user_id=owner.id,
        session_id=completed_session.id,
    )

    db_session.add(owner_registration)
    db_session.flush()

    certificate = Certificate(
        registration_id=owner_registration.id,
        validated_by=manager.id,
    )

    db_session.add(certificate)
    db_session.commit()

    db_session.refresh(owner_registration)
    db_session.refresh(certificate)

    with pytest.raises(CertificateNotOwnedError):
        get_certificate_data(
            db=db_session,
            registration_id=owner_registration.id,
            current_user=attacker,
        )

def test_get_certificate_data_raises_error_when_registration_does_not_exist(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    participant = User(
        first_name="Participant",
        last_name="User",
        email="missing-registration@example.com",
        phone_number="0550000030",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    db_session.add_all([age_category, participant])
    db_session.commit()

    db_session.refresh(participant)

    nonexistent_registration_id = uuid4()

    with pytest.raises(RegistrationNotFoundError):
        get_certificate_data(
            db=db_session,
            registration_id=nonexistent_registration_id,
            current_user=participant,
        )

def test_get_certificate_data_raises_error_when_certificate_does_not_exist(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    participant = User(
        first_name="Participant",
        last_name="User",
        email="missing-certificate@example.com",
        phone_number="0550000040",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="MISSING-CERTIFICATE-TEST",
        name="Missing Certificate Test Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed session",
        description="A completed session without an issued certificate.",
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
            participant,
            training_type,
            completed_session,
        ]
    )
    db_session.flush()

    registration = Registration(
        user_id=participant.id,
        session_id=completed_session.id,
    )

    db_session.add(registration)
    db_session.commit()

    db_session.refresh(registration)

    with pytest.raises(CertificateNotFoundError):
        get_certificate_data(
            db=db_session,
            registration_id=registration.id,
            current_user=participant,
        )
from datetime import date, time, timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db import get_db
from unittest.mock import patch

from app.auth.tokens import create_access_token
from app.models.certificate import Certificate
from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.user import User, UserRole
from app.models.age_category import AgeCategory
from app.certificates.exceptions import CertificateNotOwnedError

from app.main import app

def test_participant_can_retrieve_own_certificate(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="certificate-manager@example.com",
        phone_number="0550000011",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )
    
    participant = User(
        first_name="First",
        last_name="Participant",
        email="certificate-owner@example.com",
        phone_number="0550000010",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="CERTIFICATE-TEST",
        name="Certificate Test Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed session",
        description="A completed session for certificate retrieval testing.",
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
            manager,
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
    db_session.flush()

    certificate = Certificate(
        registration_id=registration.id,
        validated_by=manager.id,
    )

    db_session.add(certificate)
    db_session.commit()

    db_session.refresh(participant)
    db_session.refresh(registration)
    db_session.refresh(certificate)

    participant_token = create_access_token(participant.id)

    def override_get_db():
        yield db_session


    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    response = client.get(
        f"/certificates/{registration.id}",
        headers={"Authorization": f"Bearer {participant_token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert UUID(data["registration_id"]) == registration.id
    assert UUID(data["certificate_id"]) == certificate.id
    assert data["participant_first_name"] == "First"
    assert data["participant_last_name"] == "Participant"
    assert data["session_title"] == "Completed session"
    assert data["session_date"] == str(completed_session.date)
    assert data["issued_at"] is not None

    app.dependency_overrides.clear()

def test_participant_can_list_only_their_certificates(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="certificate-list-manager@example.com",
        phone_number="0550000050",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    participant = User(
        first_name="List",
        last_name="Participant",
        email="certificate-list-owner@example.com",
        phone_number="0550000051",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    other_participant = User(
        first_name="Other",
        last_name="Participant",
        email="certificate-list-other@example.com",
        phone_number="0550000052",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="CERTIFICATE-LIST-TEST",
        name="Certificate List Test Training",
    )

    older_session = TrainingSession(
        training_type=training_type,
        title="Older session",
        description="An older completed session.",
        date=date.today() - timedelta(days=10),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/older",
        instructor_name="Test Instructor",
    )

    newer_session = TrainingSession(
        training_type=training_type,
        title="Newer session",
        description="A newer completed session.",
        date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/newer",
        instructor_name="Test Instructor",
    )

    db_session.add_all(
        [
            age_category,
            manager,
            participant,
            other_participant,
            training_type,
            older_session,
            newer_session,
        ]
    )
    db_session.flush()

    participant_older_registration = Registration(
        user_id=participant.id,
        session_id=older_session.id,
    )

    participant_newer_registration = Registration(
        user_id=participant.id,
        session_id=newer_session.id,
    )

    other_registration = Registration(
        user_id=other_participant.id,
        session_id=older_session.id,
    )

    db_session.add_all(
        [
            participant_older_registration,
            participant_newer_registration,
            other_registration,
        ]
    )
    db_session.flush()

    participant_older_certificate = Certificate(
        registration_id=participant_older_registration.id,
        validated_by=manager.id,
    )

    participant_newer_certificate = Certificate(
        registration_id=participant_newer_registration.id,
        validated_by=manager.id,
    )

    other_certificate = Certificate(
        registration_id=other_registration.id,
        validated_by=manager.id,
    )

    db_session.add_all(
        [
            participant_older_certificate,
            participant_newer_certificate,
            other_certificate,
        ]
    )
    db_session.commit()

    db_session.refresh(participant)
    db_session.refresh(participant_older_registration)
    db_session.refresh(participant_newer_registration)
    db_session.refresh(participant_older_certificate)
    db_session.refresh(participant_newer_certificate)

    participant_token = create_access_token(participant.id)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    try:
        response = client.get(
            "/certificates/",
            headers={"Authorization": f"Bearer {participant_token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["session_title"] == "Newer session"
    assert data[1]["session_title"] == "Older session"

    assert UUID(data[0]["registration_id"]) == participant_newer_registration.id
    assert UUID(data[1]["registration_id"]) == participant_older_registration.id

    registration_ids = {item["registration_id"] for item in data}

    assert str(other_registration.id) not in registration_ids

def test_participant_can_download_own_certificate_pdf(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="certificate-pdf-manager@example.com",
        phone_number="0550000060",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    participant = User(
        first_name="PDF",
        last_name="Participant",
        email="certificate-pdf-owner@example.com",
        phone_number="0550000061",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="CERTIFICATE-PDF-TEST",
        name="Certificate PDF Test Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed PDF session",
        description="A completed session for certificate PDF testing.",
        date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/pdf",
        instructor_name="Test Instructor",
    )

    db_session.add_all(
        [age_category, manager, participant, training_type, completed_session]
    )
    db_session.flush()

    registration = Registration(
        user_id=participant.id,
        session_id=completed_session.id,
    )

    db_session.add(registration)
    db_session.flush()

    certificate = Certificate(
        registration_id=registration.id,
        validated_by=manager.id,
    )

    db_session.add(certificate)
    db_session.commit()

    db_session.refresh(participant)
    db_session.refresh(registration)
    db_session.refresh(certificate)

    participant_token = create_access_token(participant.id)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    fake_pdf = b"%PDF-1.7 fake certificate"

    try:
        with patch(
            "app.certificates.router.get_certificate_pdf",
            return_value=fake_pdf,
        ):
            response = client.get(
                f"/certificates/{registration.id}/pdf",
                headers={"Authorization": f"Bearer {participant_token}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.content == fake_pdf
    assert response.headers["content-type"] == "application/pdf"
    assert "certificate.pdf" in response.headers["content-disposition"]

def test_other_participant_cannot_download_certificate_pdf(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="certificate-pdf-unauthorized-manager@example.com",
        phone_number="0550000070",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    owner = User(
        first_name="Owner",
        last_name="Participant",
        email="certificate-pdf-owner-2@example.com",
        phone_number="0550000071",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    other_participant = User(
        first_name="Other",
        last_name="Participant",
        email="certificate-pdf-other@example.com",
        phone_number="0550000072",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="CERTIFICATE-PDF-UNAUTHORIZED-TEST",
        name="Certificate PDF Unauthorized Test Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed unauthorized PDF session",
        description="A completed session for unauthorized PDF testing.",
        date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://zoom.example.com/unauthorized",
        instructor_name="Test Instructor",
    )

    db_session.add_all(
        [
            age_category,
            manager,
            owner,
            other_participant,
            training_type,
            completed_session,
        ]
    )
    db_session.flush()

    registration = Registration(
        user_id=owner.id,
        session_id=completed_session.id,
    )

    db_session.add(registration)
    db_session.flush()

    certificate = Certificate(
        registration_id=registration.id,
        validated_by=manager.id,
    )

    db_session.add(certificate)
    db_session.commit()

    db_session.refresh(owner)
    db_session.refresh(other_participant)
    db_session.refresh(registration)
    db_session.refresh(certificate)

    other_participant_token = create_access_token(other_participant.id)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        response = client.get(
            f"/certificates/{registration.id}/pdf",
            headers={
                "Authorization": f"Bearer {other_participant_token}"
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
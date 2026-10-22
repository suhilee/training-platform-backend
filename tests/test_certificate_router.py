from uuid import uuid4
from datetime import date, datetime, time, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.tokens import create_access_token
from app.db import get_db
from app.main import app
from app.models.attendance import Attendance
from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.user import User, UserRole
from app.models.age_category import AgeCategory

def test_manager_can_issue_certificate_for_validated_attendance(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        code="A1",
        min_age=18,
        max_age=65,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="manager-certificate@example.com",
        phone_number="0550000000",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    participant = User(
        first_name="Participant",
        last_name="User",
        email="participant-certificate@example.com",
        phone_number="0550000001",
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
        description="A completed session for certificate testing.",
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

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    access_token = create_access_token(manager.id)

    client = TestClient(app)

    try:
        response = client.post(
            f"/certificates/registrations/{registration.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    body = response.json()

    assert body["registration_id"] == str(registration.id)
    assert body["validated_by"] == str(manager.id)

def test_participant_cannot_issue_certificate(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        code="A1",
        min_age=18,
        max_age=65,
    )

    participant = User(
        first_name="Participant",
        last_name="User",
        email="participant-forbidden@example.com",
        phone_number="0550000001",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    db_session.add_all(
        [
            age_category,
            participant,
        ]
    )
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    access_token = create_access_token(participant.id)

    client = TestClient(app)

    try:
        response = client.post(
            f"/certificates/registrations/{uuid4()}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to perform this action."
    }

def test_manager_cannot_issue_certificate_for_unvalidated_attendance(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        code="A1",
        min_age=18,
        max_age=65,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="manager-unvalidated@example.com",
        phone_number="0550000000",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    participant = User(
        first_name="Participant",
        last_name="User",
        email="participant-unvalidated@example.com",
        phone_number="0550000001",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="UNVALIDATED-CERT",
        name="Unvalidated Certificate Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed session",
        description="A completed session with unvalidated attendance.",
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

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    access_token = create_access_token(manager.id)

    client = TestClient(app)

    try:
        response = client.post(
            f"/certificates/registrations/{registration.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Attendance must be validated before issuing a certificate."
        )
    }

def test_manager_cannot_issue_duplicate_certificate(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        code="A1",
        min_age=18,
        max_age=65,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="manager-duplicate@example.com",
        phone_number="0550000000",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    participant = User(
        first_name="Participant",
        last_name="User",
        email="participant-duplicate@example.com",
        phone_number="0550000001",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code="DUPLICATE-CERT",
        name="Duplicate Certificate Training",
    )

    completed_session = TrainingSession(
        training_type=training_type,
        title="Completed session",
        description="A completed session for duplicate certificate testing.",
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

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    access_token = create_access_token(manager.id)
    client = TestClient(app)

    try:
        first_response = client.post(
            f"/certificates/registrations/{registration.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        second_response = client.post(
            f"/certificates/registrations/{registration.id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert first_response.status_code == 201

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "A certificate has already been issued for this registration."
    }

def test_manager_gets_not_found_for_missing_registration(
    db_session: Session,
) -> None:
    age_category = AgeCategory(
        code="A1",
        min_age=18,
        max_age=65,
    )

    manager = User(
        first_name="Manager",
        last_name="User",
        email="manager-missing-registration@example.com",
        phone_number="0550000000",
        date_of_birth=date(1990, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    db_session.add_all(
        [
            age_category,
            manager,
        ]
    )
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    access_token = create_access_token(manager.id)
    client = TestClient(app)

    try:
        response = client.post(
            f"/certificates/registrations/{uuid4()}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Registration not found."
    }
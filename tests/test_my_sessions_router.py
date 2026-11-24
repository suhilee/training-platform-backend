from datetime import date, datetime, time
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from sqlalchemy import inspect
from sqlalchemy.orm.attributes import NO_VALUE

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.main import app
from app.models.age_category import AgeCategory
from app.models.instructor import Instructor
from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.user import User, UserRole
from app.registrations.service import get_my_sessions


def test_list_my_sessions_returns_participant_registrations(
    monkeypatch,
) -> None:
    fake_db = object()
    fake_user = SimpleNamespace(id=uuid4())

    registration = SimpleNamespace(
        id=uuid4(),
        registered_at=datetime(2030, 1, 1, 8, 0),
    )

    training_session = SimpleNamespace(
        id=uuid4(),
        title="Introduction to Python",
        description="A beginner-friendly training session.",
        date=date(2030, 1, 1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        registered_count=25,
        instructor=SimpleNamespace(
            first_name="Jane",
            last_name="Doe",
        ),
        is_cancelled=False,
        zoom_url="https://secret.example.com/meeting",
        training_type=SimpleNamespace(
            description="Introduction to artificial intelligence",
        ),
        prerequisites=None,
    )

    service_mock = Mock(
        return_value=[
            (registration, training_session, False),
        ],
    )

    monkeypatch.setattr(
        "app.sessions.router.get_my_sessions",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: fake_user

    client = TestClient(app)

    try:
        response = client.get("/sessions/my")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["id"] == str(training_session.id)
    assert body[0]["registration_id"] == str(registration.id)
    assert body[0]["registration_state"] == "registered"
    assert body[0]["instructor_name"] == "Jane Doe"
    assert body[0]["status"] == "open"
    assert "instructor_id" not in body[0]
    assert "instructor_email" not in body[0]
    assert "instructor_phone" not in body[0]
    assert "zoom_url" not in body[0]

    service_mock.assert_called_once_with(
        db=fake_db,
        current_user=fake_user,
    )


def test_get_my_sessions_eager_loads_instructor(
    db_session,
) -> None:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    participant = User(
        first_name="Eager",
        last_name="Participant",
        email=f"eager-my-sessions-{uuid4().hex}@example.com",
        phone_number="0550000099",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
        role=UserRole.PARTICIPANT,
    )

    training_type = TrainingType(
        training_code=f"EAGER-MY-{uuid4().hex}",
        name="Eager My Sessions Training",
    )

    first_instructor = Instructor(
        first_name="First",
        last_name="Instructor",
    )

    second_instructor = Instructor(
        first_name="Second",
        last_name="Instructor",
    )

    db_session.add_all(
        [
            age_category,
            participant,
            training_type,
            first_instructor,
            second_instructor,
        ]
    )
    db_session.flush()

    first_session = TrainingSession(
        training_id=training_type.id,
        title="First eager session",
        description="A session used to verify eager loading.",
        date=date(2030, 1, 1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=10,
        zoom_url="https://example.com/first",
        instructor_id=first_instructor.id,
    )

    second_session = TrainingSession(
        training_id=training_type.id,
        title="Second eager session",
        description="A session used to verify eager loading.",
        date=date(2030, 1, 2),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=10,
        zoom_url="https://example.com/second",
        instructor_id=second_instructor.id,
    )

    db_session.add_all([first_session, second_session])
    db_session.flush()

    db_session.add_all(
        [
            Registration(
                user_id=participant.id,
                session_id=first_session.id,
            ),
            Registration(
                user_id=participant.id,
                session_id=second_session.id,
            ),
        ]
    )
    db_session.commit()
    db_session.expire_all()

    result = get_my_sessions(
        db=db_session,
        current_user=participant,
    )

    assert len(result) == 2

    for _, training_session, _ in result:
        assert (
            inspect(training_session).attrs.instructor.loaded_value
            is not NO_VALUE
        )

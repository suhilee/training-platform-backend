from datetime import date, datetime, time
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.main import app


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
        instructor_name="Jane Doe",
        is_cancelled=False,
        zoom_url="https://secret.example.com/meeting",
    )

    service_mock = Mock(
        return_value=[
            (registration, training_session, False),
        ],
    )

    monkeypatch.setattr(
        "app.registrations.router.get_my_sessions",
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
    assert body[0]["status"] == "open"
    assert "zoom_url" not in body[0]

    service_mock.assert_called_once_with(
        db=fake_db,
        current_user=fake_user,
    )

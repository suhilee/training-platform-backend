from datetime import date, time
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.sessions.exceptions import SessionNotFoundOrIneligibleError

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.main import app


def test_list_sessions_returns_eligible_sessions_without_zoom_url(
    monkeypatch,
) -> None:
    fake_db = object()
    fake_user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
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

    service_mock = Mock(return_value=[training_session])

    monkeypatch.setattr(
        "app.registrations.router.get_eligible_sessions",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: fake_user

    client = TestClient(app)

    try:
        response = client.get("/sessions")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["id"] == str(training_session.id)
    assert body[0]["title"] == "Introduction to Python"
    assert body[0]["status"] == "open"
    assert "zoom_url" not in body[0]

    service_mock.assert_called_once_with(
        db=fake_db,
        current_user=fake_user,
    )

def test_list_sessions_orders_open_sessions_by_earliest_start_time(
    monkeypatch,
) -> None:
    fake_db = object()
    fake_user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )

    later_session = SimpleNamespace(
        id=uuid4(),
        title="Later session",
        description="This happens later.",
        date=date(2030, 2, 2),
        start_time=time(14, 0),
        duration_minutes=60,
        max_capacity=100,
        registered_count=0,
        instructor_name="Jane Doe",
        is_cancelled=False,
        zoom_url="https://secret.example.com/later",
    )

    earlier_session = SimpleNamespace(
        id=uuid4(),
        title="Earlier session",
        description="This happens earlier.",
        date=date(2030, 2, 1),
        start_time=time(14, 0),
        duration_minutes=60,
        max_capacity=100,
        registered_count=0,
        instructor_name="Jane Doe",
        is_cancelled=False,
        zoom_url="https://secret.example.com/earlier",
    )

    service_mock = Mock(
        return_value=[
            later_session,
            earlier_session,
        ]
    )

    monkeypatch.setattr(
        "app.registrations.router.get_eligible_sessions",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: fake_user

    client = TestClient(app)

    try:
        response = client.get("/sessions")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert [item["id"] for item in body] == [
        str(earlier_session.id),
        str(later_session.id),
    ]

    assert [item["status"] for item in body] == [
        "open",
        "open",
    ]

def test_get_session_detail_returns_eligible_session_without_zoom_url(
    monkeypatch,
) -> None:
    fake_db = object()
    fake_user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
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

    service_mock = Mock(return_value=training_session)

    monkeypatch.setattr(
        "app.registrations.router.get_eligible_session_by_id",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: fake_user

    client = TestClient(app)

    try:
        response = client.get(f"/sessions/{training_session.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == str(training_session.id)
    assert body["title"] == "Introduction to Python"
    assert body["status"] == "open"
    assert "zoom_url" not in body

    service_mock.assert_called_once_with(
        db=fake_db,
        current_user=fake_user,
        session_id=training_session.id,
    )

def test_get_session_detail_returns_404_when_not_found_or_ineligible(
    monkeypatch,
) -> None:
    fake_db = object()
    fake_user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )
    session_id = uuid4()

    service_mock = Mock(
        side_effect=SessionNotFoundOrIneligibleError,
    )

    monkeypatch.setattr(
        "app.registrations.router.get_eligible_session_by_id",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: fake_user

    client = TestClient(app)

    try:
        response = client.get(f"/sessions/{session_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found."

    service_mock.assert_called_once_with(
        db=fake_db,
        current_user=fake_user,
        session_id=session_id,
    )

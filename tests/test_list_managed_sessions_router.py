from datetime import date, time
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.main import app
from app.models.user import UserRole

from app.sessions.schemas import SessionManagementListItemResponse


def make_managed_session(
    *,
    session_id,
    title,
    target_age_category_ids,
):
    return SessionManagementListItemResponse(
        id=session_id,
        title=title,
        date=date(2030, 1, 1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        registered_count=25,
        instructor_name="Jane Doe",
        status="open",
        target_age_category_ids=target_age_category_ids,
    )


def test_manager_can_list_all_sessions(monkeypatch) -> None:
    fake_db = object()

    manager = SimpleNamespace(
        id=uuid4(),
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    first_session = make_managed_session(
        session_id=uuid4(),
        title="Python basics",
        target_age_category_ids=[2],
    )

    second_session = make_managed_session(
        session_id=uuid4(),
        title="Advanced Python",
        target_age_category_ids=[3],
    )

    service_mock = Mock(
        return_value=[first_session, second_session],
    )

    monkeypatch.setattr(
        "app.sessions.router.get_managed_sessions",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.get("/sessions/management")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    returned_ids = {
        session["id"]
        for session in body
    }

    assert len(body) == 2
    assert str(first_session.id) in returned_ids
    assert str(second_session.id) in returned_ids

    assert body[0]["title"] == "Python basics"
    assert body[0]["registered_count"] == 25
    assert body[0]["status"] == "open"
    assert body[0]["target_age_category_ids"] == [2]

    service_mock.assert_called_once_with(
        db=fake_db,
    )


def test_participant_cannot_list_managed_sessions(
    monkeypatch,
) -> None:
    fake_db = object()

    participant = SimpleNamespace(
        id=uuid4(),
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    service_mock = Mock()

    monkeypatch.setattr(
        "app.sessions.router.get_managed_sessions",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: participant

    client = TestClient(app)

    try:
        response = client.get("/sessions/management")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403

    service_mock.assert_not_called()


def test_managed_session_list_does_not_expose_private_details(
    monkeypatch,
) -> None:
    fake_db = object()

    manager = SimpleNamespace(
        id=uuid4(),
        age_category_id=1,
        role=UserRole.SESSION_MANAGER,
    )

    managed_session = make_managed_session(
        session_id=uuid4(),
        title="Python basics",
        target_age_category_ids=[2],
    )

    service_mock = Mock(return_value=[managed_session])

    monkeypatch.setattr(
        "app.sessions.router.get_managed_sessions",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.get("/sessions/management")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1

    for session in body:
        assert "instructor_email" not in session
        assert "instructor_phone" not in session
        assert "zoom_url" not in session
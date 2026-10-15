from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.main import app

from app.registrations.exceptions import (
    ZoomAccessNotOpenError,
    NotRegisteredError,
)

def test_join_session_returns_zoom_url_for_authorised_user(
    monkeypatch,
) -> None:
    fake_db = object()
    fake_user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )
    session_id = uuid4()

    service_mock = Mock(
        return_value="https://secret.example.com/meeting",
    )

    monkeypatch.setattr(
        "app.registrations.router.join_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: fake_user

    client = TestClient(app)

    try:
        response = client.post(f"/sessions/{session_id}/join")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "zoom_url": "https://secret.example.com/meeting",
    }

    service_mock.assert_called_once_with(
        db=fake_db,
        current_user=fake_user,
        session_id=session_id,
    )

def test_join_session_returns_403_before_zoom_access_opens(
    monkeypatch,
) -> None:
    fake_db = object()
    fake_user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )
    session_id = uuid4()

    service_mock = Mock(
        side_effect=ZoomAccessNotOpenError,
    )

    monkeypatch.setattr(
        "app.registrations.router.join_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: fake_user

    client = TestClient(app)

    try:
        response = client.post(f"/sessions/{session_id}/join")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Zoom access is not available yet."
    assert "zoom_url" not in response.json()

    service_mock.assert_called_once_with(
        db=fake_db,
        current_user=fake_user,
        session_id=session_id,
    )

def test_join_session_returns_403_for_unregistered_user(
    monkeypatch,
) -> None:
    fake_db = object()
    fake_user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )
    session_id = uuid4()

    monkeypatch.setattr(
        "app.registrations.router.join_session",
        Mock(side_effect=NotRegisteredError),
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: fake_user

    client = TestClient(app)

    try:
        response = client.post(f"/sessions/{session_id}/join")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You are not registered for this session.",
    }
    assert "zoom_url" not in response.json()
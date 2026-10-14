from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.main import app
from app.registrations.exceptions import (
    NotRegisteredError,
    SessionCancelledError,
    SessionNotFoundError,
    UnregistrationClosedError,
)


def build_client(fake_db: object, fake_user: object) -> TestClient:
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    return TestClient(app)


def test_unregister_returns_no_content(monkeypatch) -> None:
    session_id = uuid4()
    fake_db = object()
    fake_user = SimpleNamespace(id=uuid4())
    service_mock = Mock()

    monkeypatch.setattr(
        "app.registrations.router.unregister_from_session",
        service_mock,
    )

    client = build_client(fake_db, fake_user)

    try:
        response = client.delete(f"/sessions/{session_id}/register")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""

    service_mock.assert_called_once_with(
        db=fake_db,
        current_user=fake_user,
        session_id=session_id,
    )


def test_unregister_returns_not_found_when_registration_missing(monkeypatch) -> None:
    session_id = uuid4()
    fake_db = object()
    fake_user = SimpleNamespace(id=uuid4())

    def raise_not_registered(**kwargs: object) -> None:
        raise NotRegisteredError

    monkeypatch.setattr(
        "app.registrations.router.unregister_from_session",
        raise_not_registered,
    )

    client = build_client(fake_db, fake_user)

    try:
        response = client.delete(f"/sessions/{session_id}/register")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "You are not registered for this session."
    }


def test_unregister_returns_not_found_when_session_missing(monkeypatch) -> None:
    session_id = uuid4()
    fake_db = object()
    fake_user = SimpleNamespace(id=uuid4())

    def raise_session_not_found(**kwargs: object) -> None:
        raise SessionNotFoundError

    monkeypatch.setattr(
        "app.registrations.router.unregister_from_session",
        raise_session_not_found,
    )

    client = build_client(fake_db, fake_user)

    try:
        response = client.delete(f"/sessions/{session_id}/register")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found."}


def test_unregister_returns_gone_when_session_cancelled(monkeypatch) -> None:
    session_id = uuid4()
    fake_db = object()
    fake_user = SimpleNamespace(id=uuid4())

    def raise_session_cancelled(**kwargs: object) -> None:
        raise SessionCancelledError

    monkeypatch.setattr(
        "app.registrations.router.unregister_from_session",
        raise_session_cancelled,
    )

    client = build_client(fake_db, fake_user)

    try:
        response = client.delete(f"/sessions/{session_id}/register")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 410
    assert response.json() == {
        "detail": "This session has been cancelled."
    }


def test_unregister_returns_forbidden_after_cutoff(monkeypatch) -> None:
    session_id = uuid4()
    fake_db = object()
    fake_user = SimpleNamespace(id=uuid4())

    def raise_unregistration_closed(**kwargs: object) -> None:
        raise UnregistrationClosedError

    monkeypatch.setattr(
        "app.registrations.router.unregister_from_session",
        raise_unregistration_closed,
    )

    client = build_client(fake_db, fake_user)

    try:
        response = client.delete(f"/sessions/{session_id}/register")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Unregistration for this session is closed."
    }
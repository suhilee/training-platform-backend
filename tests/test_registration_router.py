from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.main import app
from app.registrations.exceptions import (
    AlreadyRegisteredError,
    IneligibleForSessionError,
    RegistrationClosedError,
    SessionCancelledError,
    SessionCompletedError,
    SessionFullError,
    SessionNotFoundError,
)


def test_register_returns_409_when_session_is_full() -> None:
    db = MagicMock()
    user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )

    def override_get_db():
        return db

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)

        with patch(
            "app.registrations.router.register_for_session",
            side_effect=SessionFullError,
        ):
            response = client.post(
                f"/sessions/{uuid4()}/register",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409

    assert response.json() == {
        "detail": "This session has reached its maximum capacity.",
    }

def test_register_returns_409_when_already_registered() -> None:
    db = MagicMock()
    user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )

    def override_get_db():
        return db

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)

        with patch(
            "app.registrations.router.register_for_session",
            side_effect=AlreadyRegisteredError,
        ):
            response = client.post(
                f"/sessions/{uuid4()}/register",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409

    assert response.json() == {
        "detail": "You are already registered for this session.",
    }

def test_register_returns_403_when_ineligible() -> None:
    db = MagicMock()
    user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )

    def override_get_db():
        return db

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)

        with patch(
            "app.registrations.router.register_for_session",
            side_effect=IneligibleForSessionError,
        ):
            response = client.post(
                f"/sessions/{uuid4()}/register",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403

    assert response.json() == {
        "detail": "You are not eligible to register for this session.",
    }

def test_register_returns_404_when_session_not_found() -> None:
    db = MagicMock()
    user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )

    def override_get_db():
        return db

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)

        with patch(
            "app.registrations.router.register_for_session",
            side_effect=SessionNotFoundError,
        ):
            response = client.post(
                f"/sessions/{uuid4()}/register",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Session not found.",
    }

def test_register_returns_410_when_session_cancelled() -> None:
    db = MagicMock()
    user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )

    def override_get_db():
        return db

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)

        with patch(
            "app.registrations.router.register_for_session",
            side_effect=SessionCancelledError,
        ):
            response = client.post(
                f"/sessions/{uuid4()}/register",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 410

    assert response.json() == {
        "detail": "This session has been cancelled.",
    }

def test_register_returns_400_when_session_completed() -> None:
    db = MagicMock()
    user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )

    def override_get_db():
        return db

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)

        with patch(
            "app.registrations.router.register_for_session",
            side_effect=SessionCompletedError,
        ):
            response = client.post(
                f"/sessions/{uuid4()}/register",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 410

    assert response.json() == {
        "detail": "This session has already been completed.",
    }

def test_register_returns_403_when_registration_closed() -> None:
    db = MagicMock()
    user = SimpleNamespace(
        id=uuid4(),
        age_category_id=3,
    )

    def override_get_db():
        return db

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)

        with patch(
            "app.registrations.router.register_for_session",
            side_effect=RegistrationClosedError,
        ):
            response = client.post(
                f"/sessions/{uuid4()}/register",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Registration for this session is closed.",
    }

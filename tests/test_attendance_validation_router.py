from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.main import app
from app.models.user import UserRole

from app.attendance.exceptions import InvalidAttendanceSelectionError


def test_validate_attendance_returns_validated_count(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(
        id=uuid4(),
        role=UserRole.SESSION_MANAGER,
    )
    session_id = uuid4()
    registration_ids = [uuid4(), uuid4()]

    service_mock = Mock(return_value=2)

    monkeypatch.setattr(
        "app.sessions.router.validate_attendances",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.post(
            f"/sessions/{session_id}/attendance/validate",
            json={
                "registration_ids": [
                    str(registration_id)
                    for registration_id in registration_ids
                ],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"validated_count": 2}

    service_mock.assert_called_once_with(
        db=fake_db,
        session_id=session_id,
        registration_ids=registration_ids,
        current_manager=manager,
    )

def test_validate_attendance_rejects_participant(
    monkeypatch,
) -> None:
    fake_db = object()
    participant = SimpleNamespace(
        id=uuid4(),
        role=UserRole.PARTICIPANT,
    )
    service_mock = Mock()

    monkeypatch.setattr(
        "app.sessions.router.validate_attendances",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: participant

    client = TestClient(app)

    try:
        response = client.post(
            f"/sessions/{uuid4()}/attendance/validate",
            json={"registration_ids": [str(uuid4())]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to perform this action."
    }
    service_mock.assert_not_called()

def test_validate_attendance_returns_conflict_for_invalid_selection(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(
        id=uuid4(),
        role=UserRole.SESSION_MANAGER,
    )

    service_mock = Mock(
        side_effect=InvalidAttendanceSelectionError,
    )

    monkeypatch.setattr(
        "app.sessions.router.validate_attendances",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.post(
            f"/sessions/{uuid4()}/attendance/validate",
            json={"registration_ids": [str(uuid4())]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "One or more selected registrations are invalid, "
            "have no attendance record, or were already validated."
        )
    }
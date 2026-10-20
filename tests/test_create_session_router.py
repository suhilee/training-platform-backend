from datetime import date, time
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.main import app
from app.models.user import UserRole
from app.sessions.schemas import SessionUpdateRequest
from app.sessions.exceptions import (
    TrainingTypeNotFoundError,
    AgeCategoryNotFoundError,
    SessionNotFoundError,
    CapacityBelowRegistrationCountError,
    TargetAgeCategoryHasRegistrationsError,
)


def test_session_manager_can_create_session(monkeypatch) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    training_id = uuid4()

    created_session = SimpleNamespace(
        id=uuid4(),
        training_id=training_id,
        title="Introduction to AI",
        description="A beginner session.",
        date=date(2030, 1, 1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        registered_count=0,
        instructor_name="Jane Doe",
        is_cancelled=False,
    )

    service_mock = Mock(return_value=created_session)

    monkeypatch.setattr(
        "app.sessions.router.create_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[
        get_current_user
    ] = lambda: manager

    client = TestClient(app)

    try:
        response = client.post(
            "/sessions",
            json={
                "training_id": str(training_id),
                "title": "Introduction to AI",
                "description": "A beginner session.",
                "date": "2030-01-01",
                "start_time": "10:00:00",
                "duration_minutes": 60,
                "max_capacity": 100,
                "zoom_url": "https://secret.example.com/meeting",
                "instructor_name": "Jane Doe",
                "target_age_category_ids": [3],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == str(created_session.id)
    assert body["training_id"] == str(training_id)
    assert body["title"] == "Introduction to AI"
    assert body["registered_count"] == 0
    assert body["is_cancelled"] is False
    assert "zoom_url" not in body

    service_mock.assert_called_once()

def test_participant_cannot_create_session(monkeypatch) -> None:
    fake_db = object()
    participant = SimpleNamespace(role=UserRole.PARTICIPANT)
    service_mock = Mock()

    monkeypatch.setattr(
        "app.sessions.router.create_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: participant

    client = TestClient(app)

    try:
        response = client.post(
            "/sessions",
            json={
                "training_id": str(uuid4()),
                "title": "Introduction to AI",
                "description": "A beginner session.",
                "date": "2030-01-01",
                "start_time": "10:00:00",
                "duration_minutes": 60,
                "max_capacity": 100,
                "zoom_url": "https://secret.example.com/meeting",
                "instructor_name": "Jane Doe",
                "target_age_category_ids": [3],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to perform this action."
    )
    service_mock.assert_not_called()

def test_session_manager_gets_404_for_unknown_training_type(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)

    service_mock = Mock(side_effect=TrainingTypeNotFoundError)

    monkeypatch.setattr(
        "app.sessions.router.create_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.post(
            "/sessions",
            json={
                "training_id": str(uuid4()),
                "title": "Introduction to AI",
                "description": "A beginner session.",
                "date": "2030-01-01",
                "start_time": "10:00:00",
                "duration_minutes": 60,
                "max_capacity": 100,
                "zoom_url": "https://secret.example.com/meeting",
                "instructor_name": "Jane Doe",
                "target_age_category_ids": [3],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Training type not found."

def test_create_session_requires_exactly_one_training_type_choice(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    service_mock = Mock()

    monkeypatch.setattr(
        "app.sessions.router.create_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.post(
            "/sessions",
            json={
                "title": "Introduction to AI",
                "description": "A beginner session.",
                "date": "2030-01-01",
                "start_time": "10:00:00",
                "duration_minutes": 60,
                "max_capacity": 100,
                "zoom_url": "https://secret.example.com/meeting",
                "instructor_name": "Jane Doe",
                "target_age_category_ids": [3],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    service_mock.assert_not_called()

def test_create_session_rejects_both_training_type_choices(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    service_mock = Mock()

    monkeypatch.setattr(
        "app.sessions.router.create_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.post(
            "/sessions",
            json={
                "training_id": str(uuid4()),
                "new_training_type": {
                    "training_code": "AI-INTRO-001",
                    "name": "Introduction to AI",
                    "description": "A beginner AI training.",
                },
                "title": "Introduction to AI",
                "description": "A beginner session.",
                "date": "2030-01-01",
                "start_time": "10:00:00",
                "duration_minutes": 60,
                "max_capacity": 100,
                "zoom_url": "https://secret.example.com/meeting",
                "instructor_name": "Jane Doe",
                "target_age_category_ids": [3],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    service_mock.assert_not_called()

def test_session_manager_gets_404_for_unknown_target_age_category(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)

    service_mock = Mock(side_effect=AgeCategoryNotFoundError)

    monkeypatch.setattr(
        "app.sessions.router.create_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.post(
            "/sessions",
            json={
                "training_id": str(uuid4()),
                "title": "Introduction to AI",
                "description": "A beginner session.",
                "date": "2030-01-01",
                "start_time": "10:00:00",
                "duration_minutes": 60,
                "max_capacity": 100,
                "zoom_url": "https://secret.example.com/meeting",
                "instructor_name": "Jane Doe",
                "target_age_category_ids": [999],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Age category not found."

def test_create_session_rejects_duplicate_target_age_categories(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    service_mock = Mock()

    monkeypatch.setattr(
        "app.sessions.router.create_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.post(
            "/sessions",
            json={
                "training_id": str(uuid4()),
                "title": "Introduction to AI",
                "description": "A beginner session.",
                "date": "2030-01-01",
                "start_time": "10:00:00",
                "duration_minutes": 60,
                "max_capacity": 100,
                "zoom_url": "https://secret.example.com/meeting",
                "instructor_name": "Jane Doe",
                "target_age_category_ids": [3, 3],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    service_mock.assert_not_called()

def test_session_manager_can_cancel_session(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    session_id = uuid4()

    cancelled_session = SimpleNamespace(
        id=session_id,
        is_cancelled=True,
    )
    service_mock = Mock(return_value=cancelled_session)

    monkeypatch.setattr(
        "app.sessions.router.cancel_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.post(
            f"/sessions/{session_id}/cancel",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": str(session_id),
        "is_cancelled": True,
    }
    service_mock.assert_called_once_with(
        db=fake_db,
        session_id=session_id,
    )

def test_session_manager_gets_404_for_unknown_session_when_cancelling(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    session_id = uuid4()

    service_mock = Mock(side_effect=SessionNotFoundError)

    monkeypatch.setattr(
        "app.sessions.router.cancel_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.post(
            f"/sessions/{session_id}/cancel",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found."
    service_mock.assert_called_once_with(
        db=fake_db,
        session_id=session_id,
    )

def test_participant_cannot_cancel_session(
    monkeypatch,
) -> None:
    fake_db = object()
    participant = SimpleNamespace(role=UserRole.PARTICIPANT)
    session_id = uuid4()
    service_mock = Mock()

    monkeypatch.setattr(
        "app.sessions.router.cancel_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: participant

    client = TestClient(app)

    try:
        response = client.post(
            f"/sessions/{session_id}/cancel",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to perform this action."
    )
    service_mock.assert_not_called()

def test_session_manager_can_update_session(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    session_id = uuid4()

    updated_session = SimpleNamespace(
        id=session_id,
        training_id=uuid4(),
        title="Updated AI Session",
        description="An updated beginner session.",
        date=date(2030, 1, 2),
        start_time=time(11, 0),
        duration_minutes=90,
        max_capacity=20,
        registered_count=10,
        instructor_name="John Doe",
        is_cancelled=False,
    )
    service_mock = Mock(return_value=updated_session)

    monkeypatch.setattr(
        "app.sessions.router.update_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    payload = {
        "title": "Updated AI Session",
        "description": "An updated beginner session.",
        "date": "2030-01-02",
        "start_time": "11:00:00",
        "duration_minutes": 90,
        "max_capacity": 20,
        "zoom_url": "https://secret.example.com/updated-meeting",
        "instructor_name": "John Doe",
        "target_age_category_ids": [3, 4],
    }

    try:
        response = client.put(
            f"/sessions/{session_id}",
            json=payload,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(session_id)
    assert response.json()["title"] == "Updated AI Session"
    assert response.json()["registered_count"] == 10
    assert "zoom_url" not in response.json()

    service_mock.assert_called_once()

def test_session_manager_gets_409_when_capacity_is_below_registrations(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    session_id = uuid4()

    service_mock = Mock(
        side_effect=CapacityBelowRegistrationCountError,
    )

    monkeypatch.setattr(
        "app.sessions.router.update_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    payload = {
        "title": "Updated AI Session",
        "description": "An updated beginner session.",
        "date": "2030-01-02",
        "start_time": "11:00:00",
        "duration_minutes": 90,
        "max_capacity": 9,
        "zoom_url": "https://secret.example.com/updated-meeting",
        "instructor_name": "John Doe",
        "target_age_category_ids": [3],
    }

    try:
        response = client.put(
            f"/sessions/{session_id}",
            json=payload,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Capacity cannot be lower than the "
        "current registration count."
    )

def test_session_manager_gets_409_when_removing_category_with_registrants(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    session_id = uuid4()

    service_mock = Mock(
        side_effect=TargetAgeCategoryHasRegistrationsError,
    )

    monkeypatch.setattr(
        "app.sessions.router.update_session",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    payload = {
        "title": "Updated AI Session",
        "description": "An updated beginner session.",
        "date": "2030-01-02",
        "start_time": "11:00:00",
        "duration_minutes": 90,
        "max_capacity": 20,
        "zoom_url": "https://secret.example.com/updated-meeting",
        "instructor_name": "John Doe",
        "target_age_category_ids": [2],
    }

    try:
        response = client.put(
            f"/sessions/{session_id}",
            json=payload,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A target age category with registered "
        "participants cannot be removed."
    )

def test_session_manager_can_get_management_session_detail(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    session_id = uuid4()
    training_id = uuid4()

    training_session = SimpleNamespace(
        id=session_id,
        training_id=training_id,
        title="Introduction to AI",
        description="A beginner-friendly AI session.",
        date=date(2030, 1, 2),
        start_time=time(10, 0),
        duration_minutes=90,
        max_capacity=20,
        registered_count=5,
        zoom_url="https://secret.example.com/manager-only",
        instructor_name="John Doe",
        is_cancelled=False,
        target_categories=[
            SimpleNamespace(age_category_id=1),
            SimpleNamespace(age_category_id=3),
        ],
    )

    service_mock = Mock(
        return_value=(training_session, 3),
    )

    monkeypatch.setattr(
        "app.sessions.router.get_session_management_detail",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.get(
            f"/sessions/{session_id}/management",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["id"] == str(session_id)
    assert response_data["training_id"] == str(training_id)
    assert response_data["registered_count"] == 5
    assert response_data["attended_count"] == 3
    assert response_data["absent_count"] == 2
    assert response_data["zoom_url"] == (
        "https://secret.example.com/manager-only"
    )
    assert response_data["target_age_category_ids"] == [1, 3]

    service_mock.assert_called_once_with(
        db=fake_db,
        session_id=session_id,
    )

def test_participant_cannot_get_management_session_detail(
    monkeypatch,
) -> None:
    fake_db = object()
    participant = SimpleNamespace(role=UserRole.PARTICIPANT)
    session_id = uuid4()

    service_mock = Mock()

    monkeypatch.setattr(
        "app.sessions.router.get_session_management_detail",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: participant

    client = TestClient(app)

    try:
        response = client.get(
            f"/sessions/{session_id}/management",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to perform this action."
    )
    service_mock.assert_not_called()

def test_session_manager_gets_404_for_unknown_management_session(
    monkeypatch,
) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)
    session_id = uuid4()

    service_mock = Mock(
        side_effect=SessionNotFoundError,
    )

    monkeypatch.setattr(
        "app.sessions.router.get_session_management_detail",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.get(
            f"/sessions/{session_id}/management",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found."
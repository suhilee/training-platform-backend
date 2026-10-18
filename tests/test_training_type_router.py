from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.main import app
from app.models.user import UserRole


def test_list_training_types_returns_dropdown_items(
    monkeypatch,
) -> None:
    fake_db = object()

    manager = SimpleNamespace(
        id=uuid4(),
        role=UserRole.SESSION_MANAGER,
    )

    training_type = SimpleNamespace(
        id=uuid4(),
        training_code="AI-001",
        name="Introduction to AI",
    )

    service_mock = Mock(
        return_value=[training_type],
    )

    monkeypatch.setattr(
        "app.training_types.router.list_training_types",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.get("/training-types")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(training_type.id),
            "training_code": "AI-001",
            "name": "Introduction to AI",
        }
    ]

    service_mock.assert_called_once_with(fake_db)

def test_list_training_types_rejects_participant() -> None:
    participant = SimpleNamespace(
        id=uuid4(),
        role=UserRole.PARTICIPANT,
    )

    app.dependency_overrides[get_current_user] = lambda: participant

    client = TestClient(app)

    try:
        response = client.get("/training-types")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to perform this action.",
    }

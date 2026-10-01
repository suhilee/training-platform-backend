from datetime import date

from app.models.user import UserRole
from app.db import get_db
from fastapi.testclient import TestClient

from app.main import app

from types import SimpleNamespace
from uuid import uuid4

from app.auth.dependencies import get_current_user

def test_auth_me_rejects_missing_token() -> None:
    client = TestClient(app)
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["www-authenticate"] == "Bearer"

def test_auth_me_rejects_invalid_token() -> None:
    client = TestClient(app)

    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["www-authenticate"] == "Bearer"




def test_auth_me_returns_current_user() -> None:
    user_id = uuid4()

    def override_get_current_user():
        return SimpleNamespace(
            id=user_id,
            first_name="Souhil",
            last_name="Bensaid",
            email="participant@example.com",
            phone_number="+213555123456",
            date_of_birth=date(2000, 1, 15),
            age_category_id=4,
            wilaya="Alger",
            role=UserRole.PARTICIPANT,
        )

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)
        response = client.get("/auth/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": str(user_id),
        "first_name": "Souhil",
        "last_name": "Bensaid",
        "email": "participant@example.com",
        "phone_number": "+213555123456",
        "date_of_birth": "2000-01-15",
        "age_category_id": 4,
        "wilaya": "Alger",
        "role": "PARTICIPANT",
        }


def test_auth_me_updates_wilaya() -> None:
    user_id = uuid4()

    fake_user = SimpleNamespace(
        id=user_id,
        first_name="Test",
        last_name="Participant",
        email="participant@example.com",
        phone_number="0550000000",
        date_of_birth=date(2000, 1, 1),
        age_category_id=4,
        wilaya="Algiers",
        role="PARTICIPANT",
    )

    class FakeDb:
        def commit(self) -> None:
            pass

        def refresh(self, instance: object) -> None:
            pass

    def override_get_current_user() -> SimpleNamespace:
        return fake_user

    def override_get_db() -> FakeDb:
        return FakeDb()

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)

        response = client.patch(
            "/auth/me",
            json={"wilaya": "Oran"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["wilaya"] == "Oran"
    assert fake_user.wilaya == "Oran"

def test_auth_me_rejects_extra_profile_fields() -> None:
    fake_user = SimpleNamespace(
        id=uuid4(),
        first_name="Test",
        last_name="Participant",
        email="participant@example.com",
        phone_number="0550000000",
        date_of_birth=date(2000, 1, 1),
        age_category_id=4,
        wilaya="Algiers",
        role="PARTICIPANT",
    )

    def override_get_current_user() -> SimpleNamespace:
        return fake_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        client = TestClient(app)

        response = client.patch(
            "/auth/me",
            json={
                "wilaya": "Oran",
                "age_category_id": 7,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422

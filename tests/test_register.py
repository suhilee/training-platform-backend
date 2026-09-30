from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models.user import UserRole

from sqlalchemy.exc import IntegrityError

def test_register_creates_participant(monkeypatch) -> None:
    user_id = uuid4()

    fake_age_category = SimpleNamespace(id=5)

    fake_user = SimpleNamespace(
        id=user_id,
        name="Souhil",
        email="souhil@example.com",
        phone_number="0550123456",
        date_of_birth=date(2000, 1, 1),
        age_category_id=5,
        wilaya="Alger",
        role=UserRole.PARTICIPANT,
    )

    monkeypatch.setattr(
        "app.auth.router.get_user_by_email",
        lambda db, email: None,
    )

    monkeypatch.setattr(
        "app.auth.router.get_age_category_for_date_of_birth",
        lambda db, date_of_birth: fake_age_category,
    )

    monkeypatch.setattr(
        "app.auth.router.create_participant",
        lambda db, registration, age_category: fake_user,
    )

    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={
            "name": "Souhil",
            "email": "souhil@example.com",
            "phone_number": "0550123456",
            "date_of_birth": "2000-01-01",
            "wilaya": "Alger",
            "password": "correct-password",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == str(user_id)
    assert body["age_category_id"] == 5
    assert body["role"] == "PARTICIPANT"
    assert "password" not in body
    assert "password_hash" not in body




def test_register_fails_if_email_already_registered(monkeypatch) -> None:
    existing_user = SimpleNamespace(id=uuid4())

    monkeypatch.setattr(
        "app.auth.router.get_user_by_email",
        lambda db, email: existing_user,
    )

    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={
            "name": "Souhil",
            "email": "souhil@example.com",
            "phone_number": "0550123456",
            "date_of_birth": "2000-01-01",
            "wilaya": "Alger",
            "password": "correct-password",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email is already registered"}


def test_register_fails_if_age_not_eligible(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.auth.router.get_user_by_email",
        lambda db, email: None,
    )

    monkeypatch.setattr(
        "app.auth.router.get_age_category_for_date_of_birth",
        lambda db, date_of_birth: None,
    )

    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={
            "name": "Souhil",
            "email": "souhil@example.com",
            "phone_number": "0550123456",
            "date_of_birth": "2000-01-01",
            "wilaya": "Alger",
            "password": "correct-password",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Age is not eligible for registration"}


def test_register_converts_duplicate_email_insert_to_conflict(monkeypatch) -> None:
    fake_age_category = SimpleNamespace(id=5)

    monkeypatch.setattr(
        "app.auth.router.get_user_by_email",
        lambda db, email: None,
    )

    monkeypatch.setattr(
        "app.auth.router.get_age_category_for_date_of_birth",
        lambda db, date_of_birth: fake_age_category,
    )

    def raise_duplicate_error(db, registration, age_category):
        raise IntegrityError(
            statement=None,
            params=None,
            orig=Exception("duplicate email"),
        )

    monkeypatch.setattr(
        "app.auth.router.create_participant",
        raise_duplicate_error,
    )

    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={
            "name": "Souhil",
            "email": "souhil@example.com",
            "phone_number": "0550123456",
            "date_of_birth": "2000-01-01",
            "wilaya": "Alger",
            "password": "correct-password",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email is already registered"}
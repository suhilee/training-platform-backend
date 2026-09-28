from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.password import hash_password
from app.auth.service import get_user_by_email
from app.main import app


def test_login_returns_access_token_for_valid_credentials(monkeypatch) -> None:
    password = "correct-password"
    user = SimpleNamespace(
        id=uuid4(),
        email="participant@example.com",
        password_hash=hash_password(password),
    )

    def fake_get_user_by_email(db, email: str):
        if email == user.email:
            return user
        return None

    monkeypatch.setattr(
        "app.auth.router.get_user_by_email",
        fake_get_user_by_email,
    )

    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": password},
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["access_token"], str)
    assert body["token_type"] == "bearer"


def test_login_rejects_unknown_email(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.auth.router.get_user_by_email",
        lambda db, email: None,
    )

    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "correct-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_login_rejects_incorrect_password(monkeypatch) -> None:
    user = SimpleNamespace(
        id=uuid4(),
        email="participant@example.com",
        password_hash=hash_password("correct-password"),
    )

    monkeypatch.setattr(
        "app.auth.router.get_user_by_email",
        lambda db, email: user,
    )

    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={
            "email": user.email,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}
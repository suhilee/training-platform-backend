from fastapi.testclient import TestClient

import pytest

from app.auth.exceptions import InvalidVerificationTokenError
from app.main import app


def test_verify_email_returns_204_for_valid_token(monkeypatch):
    captured_token = None

    def fake_verify_email(db, token):
        nonlocal captured_token
        captured_token = token

    monkeypatch.setattr(
        "app.auth.router.verify_email",
        fake_verify_email,
    )

    client = TestClient(app)
    response = client.post(
        "/auth/verify-email",
        json={"token": "valid-token"},
    )

    assert response.status_code == 204
    assert captured_token == "valid-token"


def test_verify_email_returns_400_for_invalid_token(monkeypatch):
    def fake_verify_email(db, token):
        raise InvalidVerificationTokenError()

    monkeypatch.setattr(
        "app.auth.router.verify_email",
        fake_verify_email,
    )

    client = TestClient(app)
    response = client.post(
        "/auth/verify-email",
        json={"token": "invalid-token"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid or expired verification token."
    }


def test_verify_email_returns_422_for_missing_token():
    client = TestClient(app)
    response = client.post(
        "/auth/verify-email",
        json={},
    )

    assert response.status_code == 422
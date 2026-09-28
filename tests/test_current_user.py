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
            email="participant@example.com",
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
        "email": "participant@example.com",
    }
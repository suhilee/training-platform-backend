from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_logout_returns_no_content() -> None:
    response = client.post("/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
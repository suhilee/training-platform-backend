from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.tokens import create_access_token, create_refresh_token
from app.db import get_db
from app.main import app
from app.models.age_category import AgeCategory
from app.models.user import User, UserRole


def _create_refresh_test_user(db_session: Session) -> User:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    user = User(
        first_name="Refresh",
        last_name="User",
        email="refresh-user@example.com",
        phone_number="0550000080",
        date_of_birth=date(2000, 1, 1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=1,
        role=UserRole.PARTICIPANT,
    )

    db_session.add_all([age_category, user])
    db_session.commit()
    db_session.refresh(user)

    return user


def test_refresh_token_returns_new_tokens(
    db_session: Session,
) -> None:
    user = _create_refresh_test_user(db_session)

    refresh_token = create_refresh_token(user.id)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        response = client.post(
            "/auth/token/refresh",
            json={"refresh_token": refresh_token},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["access_token"] != refresh_token


def test_access_token_cannot_be_used_as_refresh_token() -> None:
    client = TestClient(app)

    access_token = create_access_token(uuid4())

    response = client.post(
        "/auth/token/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


def test_invalid_refresh_token_is_rejected() -> None:
    client = TestClient(app)

    response = client.post(
        "/auth/token/refresh",
        json={"refresh_token": "not-a-valid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


def test_refresh_token_for_nonexistent_user_is_rejected() -> None:
    client = TestClient(app)

    refresh_token = create_refresh_token(uuid4())

    response = client.post(
        "/auth/token/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"
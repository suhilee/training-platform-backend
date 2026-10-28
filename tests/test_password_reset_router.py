from datetime import datetime, timedelta, timezone, date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.service import hash_reset_token
from app.db import get_db
from app.main import app
from app.models.age_category import AgeCategory
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User


def create_user_and_request_reset(
    db_session: Session,
    email: str,
) -> str:
    age_category = AgeCategory(
        id=1,
        code="AD",
        min_age=18,
        max_age=59,
    )

    user = User(
        first_name="Test",
        last_name="User",
        email=email,
        phone_number="0550000000",
        date_of_birth=date(2000,1,1),
        wilaya="Alger",
        password_hash="not-used-in-this-test",
        age_category_id=age_category.id,
    )

    db_session.add_all([age_category, user])
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        response = client.post(
            "/auth/password/reset-request",
            json={"email": email},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    token = db_session.query(PasswordResetToken).one()

    raw_token = "known-raw-token"
    token.token_hash = hash_reset_token(raw_token)
    db_session.commit()

    return raw_token


def test_reset_request_creates_token_for_known_email(
    db_session: Session,
) -> None:
    create_user_and_request_reset(
        db_session,
        "router-known@example.com",
    )

    assert db_session.query(PasswordResetToken).count() == 1


def test_reset_request_returns_same_response_for_unknown_email(
    db_session: Session,
) -> None:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        response = client.post(
            "/auth/password/reset-request",
            json={"email": "router-unknown@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "message": (
            "If the email address is registered, "
            "a password reset link has been sent."
        )
    }
    assert db_session.query(PasswordResetToken).count() == 0


def test_reset_password_returns_204_for_valid_token(
    db_session: Session,
) -> None:
    raw_token = create_user_and_request_reset(
        db_session,
        "router-valid@example.com",
    )

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        response = client.post(
            "/auth/password/reset",
            json={
                "token": raw_token,
                "new_password": "NewPassword123",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204

    token = db_session.query(PasswordResetToken).one()
    assert token.used_at is not None


def test_reset_password_returns_400_for_invalid_token(
    db_session: Session,
) -> None:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        response = client.post(
            "/auth/password/reset",
            json={
                "token": "invalid-token",
                "new_password": "NewPassword123",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400


def test_reset_password_returns_400_for_reused_token(
    db_session: Session,
) -> None:
    raw_token = create_user_and_request_reset(
        db_session,
        "router-reused@example.com",
    )

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        first_response = client.post(
            "/auth/password/reset",
            json={
                "token": raw_token,
                "new_password": "NewPassword123",
            },
        )

        second_response = client.post(
            "/auth/password/reset",
            json={
                "token": raw_token,
                "new_password": "AnotherPassword123",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert first_response.status_code == 204
    assert second_response.status_code == 400


def test_reset_password_returns_400_for_expired_token(
    db_session: Session,
) -> None:
    raw_token = create_user_and_request_reset(
        db_session,
        "router-expired@example.com",
    )

    token = db_session.query(PasswordResetToken).one()
    token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        response = client.post(
            "/auth/password/reset",
            json={
                "token": raw_token,
                "new_password": "NewPassword123",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
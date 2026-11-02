from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.auth.exceptions import InvalidVerificationTokenError
from app.auth.service import verify_email


def make_db(token, user):
    queries = []

    def fake_query(model):
        class FakeQuery:
            def filter(self, *args, **kwargs):
                return self

            def first(self):
                if not queries:
                    queries.append("token")
                    return token
                queries.append("user")
                return user

        return FakeQuery()

    return SimpleNamespace(query=fake_query, commit=lambda: None)


def test_verify_email_marks_user_verified_and_token_used():
    now = datetime.now(timezone.utc)

    user = SimpleNamespace(
        id=uuid4(),
        email_verified=False,
    )

    token = SimpleNamespace(
        user_id=user.id,
        token_hash="hashed-token",
        expires_at=now + timedelta(hours=1),
        used_at=None,
    )

    db = make_db(token, user)

    verify_email(db, "raw-token")

    assert user.email_verified is True
    assert token.used_at is not None


def test_verify_email_rejects_unknown_token():
    db = make_db(token=None, user=None)

    with pytest.raises(InvalidVerificationTokenError):
        verify_email(db, "unknown-token")


def test_verify_email_rejects_already_used_token():
    now = datetime.now(timezone.utc)

    user = SimpleNamespace(
        id=uuid4(),
        email_verified=False,
    )

    token = SimpleNamespace(
        user_id=user.id,
        token_hash="hashed-token",
        expires_at=now + timedelta(hours=1),
        used_at=now - timedelta(minutes=5),
    )

    db = make_db(token, user)

    with pytest.raises(InvalidVerificationTokenError):
        verify_email(db, "raw-token")


def test_verify_email_rejects_expired_token():
    now = datetime.now(timezone.utc)

    user = SimpleNamespace(
        id=uuid4(),
        email_verified=False,
    )

    token = SimpleNamespace(
        user_id=user.id,
        token_hash="hashed-token",
        expires_at=now - timedelta(hours=1),
        used_at=None,
    )

    db = make_db(token, user)

    with pytest.raises(InvalidVerificationTokenError):
        verify_email(db, "raw-token")


def test_verify_email_rejects_missing_user():
    now = datetime.now(timezone.utc)

    token = SimpleNamespace(
        user_id=uuid4(),
        token_hash="hashed-token",
        expires_at=now + timedelta(hours=1),
        used_at=None,
    )

    db = make_db(token, user=None)

    with pytest.raises(InvalidVerificationTokenError):
        verify_email(db, "raw-token")


def test_verify_email_rejects_already_verified_user():
    now = datetime.now(timezone.utc)

    user = SimpleNamespace(
        id=uuid4(),
        email_verified=True,
    )

    token = SimpleNamespace(
        user_id=user.id,
        token_hash="hashed-token",
        expires_at=now + timedelta(hours=1),
        used_at=None,
    )

    db = make_db(token, user)

    with pytest.raises(InvalidVerificationTokenError):
        verify_email(db, "raw-token")
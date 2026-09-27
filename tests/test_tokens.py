from uuid import uuid4

import jwt
import pytest

from app.auth.tokens import create_access_token, decode_access_token


def test_create_and_decode_access_token() -> None:
    user_id = uuid4()

    token = create_access_token(user_id)
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert "exp" in payload


def test_decode_access_token_rejects_tampered_token() -> None:
    token = create_access_token(uuid4())
    tampered_token = f"{token}tampered"

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered_token)
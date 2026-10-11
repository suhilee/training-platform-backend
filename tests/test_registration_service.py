from datetime import date, time
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import MagicMock

from app.registrations.service import register_for_session

import pytest

from app.registrations.exceptions import IneligibleForSessionError


def test_register_for_session_creates_registration() -> None:
    user_id = uuid4()
    session_id = uuid4()

    current_user = SimpleNamespace(
        id=user_id,
        age_category_id=3,
    )

    training_session = SimpleNamespace(
        id=session_id,
        is_cancelled=False,
        date=date(2030, 1, 1),
        start_time=time(10, 0),
        duration_minutes=60,
        target_categories=[
            SimpleNamespace(age_category_id=3),
        ],
        registered_count=0,
        max_capacity=100,
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = training_session

    duplicate_query_result = MagicMock()
    duplicate_query_result.scalar_one_or_none.return_value = None

    db = MagicMock()
    db.execute.side_effect = [
        session_query_result,
        duplicate_query_result,
    ]

    registration = register_for_session(
    db=db,
    current_user=current_user,
    session_id=session_id,
    )

    assert registration.user_id == user_id
    assert registration.session_id == session_id
    assert training_session.registered_count == 1

    db.add.assert_called_once_with(registration)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(registration)

def test_register_for_session_rejects_ineligible_user() -> None:
    user_id = uuid4()
    session_id = uuid4()

    current_user = SimpleNamespace(
        id=user_id,
        age_category_id=4,
    )

    training_session = SimpleNamespace(
        id=session_id,
        is_cancelled=False,
        date=date(2030, 1, 1),
        start_time=time(10, 0),
        duration_minutes=60,
        target_categories=[
            SimpleNamespace(age_category_id=3),
        ],
        registered_count=0,
        max_capacity=100,
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = training_session

    db = MagicMock()
    db.execute.return_value = session_query_result

    with pytest.raises(IneligibleForSessionError):
        register_for_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    assert training_session.registered_count == 0
    db.execute.assert_called_once()
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()

    
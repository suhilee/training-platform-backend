from datetime import date, time, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import MagicMock

from app.registrations.service import register_for_session
from app.registrations.service import unregister_from_session

import pytest

from app.models.registration import Registration
from app.registrations.exceptions import (
    AlreadyRegisteredError,
    IneligibleForSessionError,
    SessionCancelledError,
    SessionFullError,
    SessionNotFoundError,
    SessionCompletedError,
    RegistrationClosedError,
    UnregistrationClosedError,
    NotRegisteredError,
)

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

def test_register_rejects_at_exactly_one_hour_before_session() -> None:
    now = datetime.now()

    session = SimpleNamespace(
        id=uuid4(),
        start_time=(now + timedelta(hours=1)).time(),
        is_cancelled=False,
        date=now.date(),
        duration_minutes=60,
        target_categories=[SimpleNamespace(age_category_id=1)],
        registered_count=0,
        max_capacity=10,
    )

    user = SimpleNamespace(
        id=uuid4(),
        age_category_id=1,
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = session

    db = MagicMock()
    db.execute.side_effect = [
        session_query_result,
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
    ]

    with pytest.raises(RegistrationClosedError):
        register_for_session(
            db=db,
            current_user=user,
            session_id=session.id,
        )

def test_register_rejects_duplicate_registration() -> None:
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
        registered_count=3,
        max_capacity=100,
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = training_session

    duplicate_query_result = MagicMock()
    duplicate_query_result.scalar_one_or_none.return_value = Registration(
        id=uuid4(),
        user_id=user_id,
        session_id=session_id,
        registered_at=datetime.now() - timedelta(minutes=1),
    )

    db = MagicMock()
    db.execute.side_effect = [
        session_query_result,
        duplicate_query_result,
    ]


    with pytest.raises(AlreadyRegisteredError):
        register_for_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    assert training_session.registered_count == 3
    db.add.assert_not_called()

def test_register_rejects_full_session() -> None:
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
        registered_count=100,
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
    with pytest.raises(SessionFullError):
        register_for_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    assert training_session.registered_count == 100
    db.add.assert_not_called()
    db.commit.assert_not_called()

def test_register_rejects_completed_session() -> None:
    user_id = uuid4()
    session_id = uuid4()

    current_user = SimpleNamespace(
        id=user_id,
        age_category_id=3,
    )

    training_session = SimpleNamespace(
        id=session_id,
        is_cancelled=False,
        date=date(2020, 1, 1),
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

    with pytest.raises(SessionCompletedError):
        register_for_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    assert training_session.registered_count == 0
    db.add.assert_not_called()
    db.commit.assert_not_called()

def test_register_rejects_cancelled_session() -> None:
    user_id = uuid4()
    session_id = uuid4()

    current_user = SimpleNamespace(
        id=user_id,
        age_category_id=3,
    )

    training_session = SimpleNamespace(
        id=session_id,
        is_cancelled=True,
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

    with pytest.raises(SessionCancelledError):
        register_for_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    assert training_session.registered_count == 0
    db.add.assert_not_called()
    db.commit.assert_not_called()

def test_register_rejects_nonexistent_session() -> None:
    user_id = uuid4()
    session_id = uuid4()

    current_user = SimpleNamespace(
        id=user_id,
        age_category_id=3,
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = None

    db = MagicMock()
    db.execute.return_value = session_query_result

    with pytest.raises(SessionNotFoundError):
        register_for_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )
    # to assert that it did not perform extra queries after failing to find the session
    assert db.execute.call_count == 1

    db.add.assert_not_called()
    db.commit.assert_not_called()

# TEST CASES FOR UNREGISTRATION
def test_unregister_success() -> None:
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
        registered_count=3,
        max_capacity=100,
    )

    existing_registration = Registration(
        id=uuid4(),
        user_id=user_id,
        session_id=session_id,
        registered_at=datetime.now() - timedelta(minutes=1),
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = training_session

    registration_query_result = MagicMock()
    registration_query_result.scalar_one_or_none.return_value = existing_registration

    db = MagicMock()
    db.execute.side_effect = [
        session_query_result,
        registration_query_result,
    ]

    # Call the unregister function
    unregister_from_session(
        db=db,
        current_user=current_user,
        session_id=session_id,
    )

    assert training_session.registered_count == 2
    db.delete.assert_called_once_with(existing_registration)
    db.commit.assert_called_once()

def test_unregister_rejects_after_cutoff() -> None:
    now = datetime.now()
    user_id = uuid4()
    session_id = uuid4()

    current_user = SimpleNamespace(
        id=user_id,
        age_category_id=3,
    )

    training_session = SimpleNamespace(
        id=uuid4(),
        start_time=(now + timedelta(hours=1)).time(),
        is_cancelled=False,
        date=now.date(),
        duration_minutes=60,
        target_categories=[SimpleNamespace(age_category_id=1)],
        registered_count=3,
        max_capacity=10,
    )

    existing_registration = Registration(
        id=uuid4(),
        user_id=user_id,
        session_id=session_id,
        registered_at=datetime.now() - timedelta(minutes=1),
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = training_session

    registration_query_result = MagicMock()
    registration_query_result.scalar_one_or_none.return_value = existing_registration

    db = MagicMock()
    db.execute.side_effect = [
        session_query_result,
        registration_query_result,
    ]

    # Mock datetime to simulate being after the cutoff time
    with pytest.raises(UnregistrationClosedError):
        unregister_from_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    assert training_session.registered_count == 3
    db.delete.assert_not_called()
    db.commit.assert_not_called()

def test_unregister_rejects_nonexistent_registration() -> None:
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
        registered_count=3,
        max_capacity=100,
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = training_session

    registration_query_result = MagicMock()
    registration_query_result.scalar_one_or_none.return_value = None

    db = MagicMock()
    db.execute.side_effect = [
        session_query_result,
        registration_query_result,
    ]

    with pytest.raises(NotRegisteredError):
        unregister_from_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    assert training_session.registered_count == 3
    db.delete.assert_not_called()
    db.commit.assert_not_called()

def test_unregister_rejects_cancelled_session() -> None:
    user_id = uuid4()
    session_id = uuid4()

    current_user = SimpleNamespace(
        id=user_id,
        age_category_id=3,
    )

    training_session = SimpleNamespace(
        id=session_id,
        is_cancelled=True,
        date=date(2030, 1, 1),
        start_time=time(10, 0),
        duration_minutes=60,
        target_categories=[
            SimpleNamespace(age_category_id=3),
        ],
        registered_count=3,
        max_capacity=100,
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = training_session

    db = MagicMock()
    db.execute.return_value = session_query_result

    with pytest.raises(SessionCancelledError):
        unregister_from_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    assert db.execute.call_count == 1
    assert training_session.registered_count == 3
    db.delete.assert_not_called()
    db.commit.assert_not_called()

def test_unregister_rejects_nonexistent_session() -> None:
    user_id = uuid4()
    session_id = uuid4()

    current_user = SimpleNamespace(
        id=user_id,
        age_category_id=3,
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = None

    db = MagicMock()
    db.execute.return_value = session_query_result

    with pytest.raises(SessionNotFoundError):
        unregister_from_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )
    # to assert that it did not perform extra queries after failing to find the session
    assert db.execute.call_count == 1

    db.delete.assert_not_called()
    db.commit.assert_not_called()

def test_unregister_rejects_zero_registration_count() -> None:
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

    existing_registration = Registration(
        id=uuid4(),
        user_id=user_id,
        session_id=session_id,
        registered_at=datetime.now() - timedelta(minutes=1),
    )

    session_query_result = MagicMock()
    session_query_result.scalar_one_or_none.return_value = training_session

    registration_query_result = MagicMock()
    registration_query_result.scalar_one_or_none.return_value = existing_registration

    db = MagicMock()
    db.execute.side_effect = [
        session_query_result,
        registration_query_result,
    ]

    with pytest.raises(RuntimeError):
        unregister_from_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    assert training_session.registered_count == 0
    db.delete.assert_not_called()
    db.commit.assert_not_called()


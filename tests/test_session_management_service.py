import pytest
from uuid import uuid4
from unittest.mock import Mock, call
from datetime import datetime

from app.sessions.exceptions import (
    TrainingTypeNotFoundError,
    AgeCategoryNotFoundError,
    SessionNotFoundError,
)

from app.sessions.management_service import create_session, cancel_session
from app.sessions.schemas import (
    SessionCreateRequest,
    NewTrainingTypeInput
)

from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.age_category import AgeCategory


def test_create_session_rejects_unknown_training_type() -> None:
    training_id = uuid4()

    request = SessionCreateRequest(
        training_id=training_id,
        title="Introduction to AI",
        description="A beginner session.",
        date="2030-01-01",
        start_time="10:00:00",
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://example.com/meeting",
        instructor_name="Jane Doe",
        target_age_category_ids=[3],
    )

    db = Mock()
    db.get.return_value = None

    with pytest.raises(TrainingTypeNotFoundError):
        create_session(db=db, request=request)

    db.get.assert_called_once_with(
        TrainingType,
        training_id,
    )

def test_create_session_uses_existing_training_type() -> None:
    training_id = uuid4()

    request = SessionCreateRequest(
        training_id=training_id,
        title="Introduction to AI",
        description="A beginner session.",
        date="2030-01-01",
        start_time="10:00:00",
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://example.com/meeting",
        instructor_name="Jane Doe",
        target_age_category_ids=[3],
    )

    existing_training_type = TrainingType(
        id=training_id,
        training_code="AI-INTRO-001",
        name="Introduction to AI",
        description="A beginner AI training.",
    )

    db = Mock()
    db.get.return_value = existing_training_type

    result = create_session(db=db, request=request)

    assert isinstance(result, TrainingSession)
    assert result.training_type is existing_training_type
    assert result.title == request.title
    assert result.description == request.description
    assert result.date == request.date
    assert result.start_time == request.start_time
    assert result.duration_minutes == request.duration_minutes
    assert result.max_capacity == request.max_capacity
    assert result.zoom_url == request.zoom_url
    assert result.instructor_name == request.instructor_name

    db.get.assert_has_calls(
        [
            call(TrainingType, training_id),
            call(AgeCategory, 3),
        ]
    )
    assert db.get.call_count == 2
    db.add.assert_called_once_with(result)

def test_create_session_creates_new_training_type() -> None:
    request = SessionCreateRequest(
        new_training_type=NewTrainingTypeInput(
            training_code="AI-INTRO-001",
            name="Introduction to AI",
            description="A beginner AI training.",
        ),
        title="Introduction to AI — January session",
        description="A beginner session.",
        date="2030-01-01",
        start_time="10:00:00",
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://example.com/meeting",
        instructor_name="Jane Doe",
        target_age_category_ids=[3],
    )

    db = Mock()

    result = create_session(db=db, request=request)

    assert isinstance(result, TrainingSession)
    assert result.training_type.training_code == "AI-INTRO-001"
    assert result.training_type.name == "Introduction to AI"
    assert result.training_type.description == "A beginner AI training."

    db.get.assert_called_once_with(AgeCategory, 3)
    assert db.add.call_count == 2
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)

def test_create_session_rejects_unknown_target_age_category() -> None:
    training_id = uuid4()

    request = SessionCreateRequest(
        training_id=training_id,
        title="Introduction to AI",
        description="A beginner session.",
        date="2030-01-01",
        start_time="10:00:00",
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://example.com/meeting",
        instructor_name="Jane Doe",
        target_age_category_ids=[999],
    )

    existing_training_type = TrainingType(
        id=training_id,
        training_code="AI-INTRO-001",
        name="Introduction to AI",
        description="A beginner AI training.",
    )

    db = Mock()

    def get_side_effect(model, object_id):
        if model is TrainingType:
            return existing_training_type

        if model is AgeCategory:
            return None

        raise AssertionError(f"Unexpected model: {model}")

    db.get.side_effect = get_side_effect

    with pytest.raises(AgeCategoryNotFoundError):
        create_session(db=db, request=request)

    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()

def test_cancel_session_marks_existing_session_as_cancelled(
    monkeypatch,
) -> None:
    session_id = uuid4()
    training_session = Mock(
        id=session_id,
        is_cancelled=False,
        cancelled_at=None,
    )
    db = Mock()
    db.get.return_value = training_session

    cancelled_at = datetime(2030, 1, 1, 9, 30, 0)
    monkeypatch.setattr(
        "app.sessions.management_service.datetime",
        Mock(now=Mock(return_value=cancelled_at)),
    )

    result = cancel_session(
        db=db,
        session_id=session_id,
    )

    assert result is training_session
    assert training_session.is_cancelled is True
    assert training_session.cancelled_at == cancelled_at
    db.get.assert_called_once_with(TrainingSession, session_id)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(training_session)

def test_cancel_session_rejects_unknown_session() -> None:
    session_id = uuid4()
    db = Mock()
    db.get.return_value = None

    with pytest.raises(SessionNotFoundError):
        cancel_session(
            db=db,
            session_id=session_id,
        )

    db.get.assert_called_once_with(TrainingSession, session_id)
    db.commit.assert_not_called()
    db.refresh.assert_not_called()

def test_cancel_session_preserves_existing_cancellation_time(
    monkeypatch,
) -> None:
    session_id = uuid4()
    original_cancelled_at = datetime(2030, 1, 1, 9, 30, 0)

    training_session = Mock(
        id=session_id,
        is_cancelled=True,
        cancelled_at=original_cancelled_at,
    )
    db = Mock()
    db.get.return_value = training_session

    later_time = datetime(2030, 1, 2, 9, 30, 0)
    monkeypatch.setattr(
        "app.sessions.management_service.datetime",
        Mock(now=Mock(return_value=later_time)),
    )

    result = cancel_session(
        db=db,
        session_id=session_id,
    )

    assert result is training_session
    assert training_session.is_cancelled is True
    assert training_session.cancelled_at == original_cancelled_at
    db.commit.assert_not_called()
    db.refresh.assert_not_called()
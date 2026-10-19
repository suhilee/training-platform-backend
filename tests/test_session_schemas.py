from datetime import date, time
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.sessions.schemas import SessionCreateRequest


def valid_session_data() -> dict:
    return {
        "title": "Introduction to AI",
        "description": "A beginner session.",
        "date": date(2030, 1, 1),
        "start_time": time(10, 0),
        "duration_minutes": 60,
        "max_capacity": 100,
        "zoom_url": "https://example.com/meeting",
        "instructor_name": "Jane Doe",
        "target_age_category_ids": [3],
    }


def test_session_create_request_rejects_missing_training_choice() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        SessionCreateRequest(**valid_session_data())


def test_session_create_request_rejects_both_training_choices() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        SessionCreateRequest(
            **valid_session_data(),
            training_id=uuid4(),
            new_training_type={
                "training_code": "AI-001",
                "name": "Introduction to AI",
            },
        )


def test_session_create_request_accepts_existing_training() -> None:
    training_id = uuid4()

    request = SessionCreateRequest(
        **valid_session_data(),
        training_id=training_id,
    )

    assert request.training_id == training_id
    assert request.new_training_type is None

def test_session_create_request_accepts_new_training_type() -> None:
    request = SessionCreateRequest(
        **valid_session_data(),
        new_training_type={
            "training_code": "AI-001",
            "name": "Introduction to AI",
            "description": "A reusable beginner AI training.",
        },
    )

    assert request.training_id is None
    assert request.new_training_type is not None
    assert request.new_training_type.training_code == "AI-001"
    assert request.new_training_type.name == "Introduction to AI"
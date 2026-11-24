from datetime import date, time

from app.sessions.management_service import get_managed_sessions

from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.age_category import AgeCategory
from app.models.instructor import Instructor
from app.models.session_target_category import SessionTargetCategory


def test_get_managed_sessions_returns_all_sessions(
    db_session,
) -> None:
    training_type = TrainingType(
        training_code="AI-INTRO-001",
        name="Introduction to AI",
        description="A beginner AI training.",
    )

    age_category_two = AgeCategory(
        id=2,
        code="C2",
        min_age=7,
        max_age=10,
    )

    age_category_three = AgeCategory(
        id=3,
        code="C3",
        min_age=11,
        max_age=14,
    )

    first_instructor = Instructor(
        first_name="Jane",
        last_name="Doe",
    )

    second_instructor = Instructor(
        first_name="John",
        last_name="Doe",
    )

    db_session.add_all(
        [
            training_type,
            age_category_two,
            age_category_three,
            first_instructor,
            second_instructor,
        ]
    )
    db_session.flush()

    first_session = TrainingSession(
        training_id=training_type.id,
        title="Python basics",
        description="A beginner Python session.",
        date=date(2030, 1, 1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=100,
        zoom_url="https://example.com/first-meeting",
        instructor_id=first_instructor.id,
        target_categories=[
            SessionTargetCategory(
                age_category_id=age_category_two.id,
            ),
        ],
    )

    second_session = TrainingSession(
        training_id=training_type.id,
        title="Advanced Python",
        description="An advanced Python session.",
        date=date(2030, 1, 2),
        start_time=time(14, 0),
        duration_minutes=90,
        max_capacity=50,
        zoom_url="https://example.com/second-meeting",
        instructor_id=second_instructor.id,
        target_categories=[
            SessionTargetCategory(
                age_category_id=age_category_three.id,
            ),
        ],
    )

    db_session.add_all(
        [
            first_session,
            second_session,
        ]
    )
    db_session.commit()

    result = get_managed_sessions(db=db_session)

    assert len(result) == 2

    returned_ids = {
        managed_session.id
        for managed_session in result
    }

    assert first_session.id in returned_ids
    assert second_session.id in returned_ids

    first_result = next(
        managed_session
        for managed_session in result
        if managed_session.id == first_session.id
    )

    second_result = next(
        managed_session
        for managed_session in result
        if managed_session.id == second_session.id
    )

    assert first_result.title == "Python basics"
    assert first_result.instructor_id == first_instructor.id
    assert first_result.instructor_name == "Jane Doe"
    assert first_result.status == "open"
    assert first_result.target_age_category_ids == [
        age_category_two.id,
    ]

    assert second_result.title == "Advanced Python"
    assert second_result.instructor_id == second_instructor.id
    assert second_result.instructor_name == "John Doe"
    assert second_result.status == "open"
    assert second_result.target_age_category_ids == [
        age_category_three.id,
    ]
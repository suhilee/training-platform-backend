from datetime import date, time
from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy import inspect
from sqlalchemy.orm.attributes import NO_VALUE

from app.models.age_category import AgeCategory
from app.models.instructor import Instructor
from app.models.session import Session as TrainingSession
from app.models.session_target_category import SessionTargetCategory
from app.models.training_type import TrainingType
from app.sessions.service import get_eligible_sessions


def test_get_eligible_sessions_returns_query_results() -> None:
    current_user = SimpleNamespace(age_category_id=3)

    first_session = SimpleNamespace(id="first")
    second_session = SimpleNamespace(id="second")

    query_result = MagicMock()
    query_result.unique.return_value.scalars.return_value.all.return_value = [
        first_session,
        second_session,
    ]

    db = MagicMock()
    db.execute.return_value = query_result

    result = get_eligible_sessions(
        db=db,
        current_user=current_user,
    )

    assert result == [first_session, second_session]
    db.execute.assert_called_once()


def test_get_eligible_sessions_eager_loads_instructor(
    db_session,
) -> None:
    age_category = AgeCategory(
        id=3,
        code="C3",
        min_age=11,
        max_age=14,
    )

    training_type = TrainingType(
        training_code="EAGER-ELIGIBLE",
        name="Eager Eligible Training",
    )

    first_instructor = Instructor(
        first_name="First",
        last_name="Instructor",
    )

    second_instructor = Instructor(
        first_name="Second",
        last_name="Instructor",
    )

    db_session.add_all(
        [
            age_category,
            training_type,
            first_instructor,
            second_instructor,
        ]
    )
    db_session.flush()

    first_session = TrainingSession(
        training_id=training_type.id,
        title="First eager session",
        description="A session used to verify eager loading.",
        date=date(2030, 1, 1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=10,
        zoom_url="https://example.com/first",
        instructor_id=first_instructor.id,
        target_categories=[
            SessionTargetCategory(
                age_category_id=age_category.id,
            ),
        ],
    )

    second_session = TrainingSession(
        training_id=training_type.id,
        title="Second eager session",
        description="A session used to verify eager loading.",
        date=date(2030, 1, 2),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=10,
        zoom_url="https://example.com/second",
        instructor_id=second_instructor.id,
        target_categories=[
            SessionTargetCategory(
                age_category_id=age_category.id,
            ),
        ],
    )

    db_session.add_all([first_session, second_session])
    db_session.commit()
    db_session.expire_all()

    result = get_eligible_sessions(
        db=db_session,
        current_user=SimpleNamespace(
            age_category_id=age_category.id,
        ),
    )

    assert len(result) == 2

    for training_session in result:
        assert (
            inspect(training_session).attrs.instructor.loaded_value
            is not NO_VALUE
        )

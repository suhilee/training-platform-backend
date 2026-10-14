from datetime import date, datetime, time
from types import SimpleNamespace

from app.sessions.status import get_session_status


def make_session(
    *,
    is_cancelled: bool = False,
    session_date: date = date(2030, 1, 1),
    start_time: time = time(10, 0),
    duration_minutes: int = 60,
    registered_count: int = 0,
    max_capacity: int = 100,
) -> SimpleNamespace:
    return SimpleNamespace(
        is_cancelled=is_cancelled,
        date=session_date,
        start_time=start_time,
        duration_minutes=duration_minutes,
        registered_count=registered_count,
        max_capacity=max_capacity,
    )


def test_cancelled_session_status_overrides_other_conditions() -> None:
    training_session = make_session(
        is_cancelled=True,
        registered_count=100,
        max_capacity=100,
    )

    now = datetime(2030, 1, 1, 12, 0)

    status = get_session_status(training_session, now)

    assert status == "cancelled"


def test_session_is_completed_at_its_end_time() -> None:
    training_session = make_session()

    now = datetime(2030, 1, 1, 11, 0)

    status = get_session_status(training_session, now)

    assert status == "completed"

def test_session_is_running_from_start_until_end() -> None:
    training_session = make_session()

    now = datetime(2030, 1, 1, 10, 30)

    status = get_session_status(training_session, now)

    assert status == "running"

def test_session_is_full_before_start_when_capacity_reached() -> None:
    training_session = make_session(
        registered_count=100,
        max_capacity=100,
    )

    now = datetime(2030, 1, 1, 9, 0)

    status = get_session_status(training_session, now)

    assert status == "full"

def test_session_is_open_before_start_when_capacity_remains() -> None:
    training_session = make_session(
        registered_count=99,
        max_capacity=100,
    )

    now = datetime(2030, 1, 1, 9, 0)

    status = get_session_status(training_session, now)

    assert status == "open"

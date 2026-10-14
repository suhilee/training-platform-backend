from datetime import datetime, timedelta

from app.models.session import Session


def get_session_status(
    training_session: Session,
    now: datetime,
) -> str:
    if training_session.is_cancelled:
        return "cancelled"

    session_start = datetime.combine(
        training_session.date,
        training_session.start_time,
    )
    session_end = session_start + timedelta(
        minutes=training_session.duration_minutes,
    )

    if now >= session_end:
        return "completed"

    if now >= session_start:
        return "running"
    
    if training_session.registered_count >= training_session.max_capacity:
        return "full"

    return "open"

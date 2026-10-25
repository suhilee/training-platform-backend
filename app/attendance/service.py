from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.session import Session as TrainingSession
from app.models.attendance import Attendance
from app.models.registration import Registration
from app.models.certificate import Certificate
from app.attendance.exceptions import (
    InvalidAttendanceSelectionError,
    SessionNotFoundError,
    SessionNotCompletedError,
)

def validate_attendances(
    db: Session,
    session_id: UUID,
    registration_ids: list[UUID],
    current_manager: User,
) -> int:
    training_session = db.get(TrainingSession, session_id)

    if training_session is None:
        raise SessionNotFoundError

    session_end = datetime.combine(
        training_session.date,
        training_session.start_time,
    ) + timedelta(minutes=training_session.duration_minutes)

    if training_session.is_cancelled or datetime.now() < session_end:
        raise SessionNotCompletedError
    
    statement = (
        select(Attendance)
        .join(
            Registration,
            Attendance.registration_id == Registration.id,
        )
        .where(
            Registration.session_id == session_id,
            Attendance.registration_id.in_(registration_ids),
            Attendance.validated_at.is_(None),
        )
    )

    attendances = list(db.execute(statement).scalars().all())

    if len(attendances) != len(registration_ids):
        raise InvalidAttendanceSelectionError
    
    validated_at = datetime.now()

    for attendance in attendances:
        attendance.validated_at = validated_at
        attendance.validated_by = current_manager.id

        certificate = Certificate(
            registration_id=attendance.registration_id,
            validated_by=current_manager.id,
        )
        
        db.add(certificate)

    db.commit()

    return len(attendances)
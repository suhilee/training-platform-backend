from uuid import UUID

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.session_target_category import SessionTargetCategory
from app.models.user import User

from app.registrations.exceptions import (
    AlreadyRegisteredError,
    IneligibleForSessionError,
    SessionCancelledError,
    SessionFullError,
    SessionNotFoundError,
    SessionCompletedError,
)

def register_for_session(
    db: Session,
    current_user: User,
    session_id: UUID,
) -> Registration:
    session_statement = (
        select(TrainingSession)
        .where(TrainingSession.id == session_id)
        .with_for_update()
    )

    training_session = db.execute(session_statement).scalar_one_or_none()

    if training_session is None:
        raise SessionNotFoundError

    if training_session.is_cancelled:
        raise SessionCancelledError

    target_category_ids = {
    category.age_category_id
    for category in training_session.target_categories
    }

    if current_user.age_category_id not in target_category_ids:
        raise IneligibleForSessionError

    session_start = datetime.combine(
    training_session.date,
    training_session.start_time,
    )

    session_end = session_start + timedelta(
        minutes=training_session.duration_minutes,
    )

    if datetime.now() >= session_end:
        raise SessionCompletedError
    
    if training_session.registered_count >= training_session.max_capacity:
        raise SessionFullError

    registration_statement = (
            select(Registration)
            .where(Registration.session_id == session_id)
            .where(Registration.user_id == current_user.id)
    )

    existing_registration = db.execute(registration_statement).scalar_one_or_none()

    if existing_registration is not None:
        raise AlreadyRegisteredError

    registration = Registration(
    user_id=current_user.id,
    session_id=training_session.id,
    )

    # we increment the registered_count and the registration at the same time
    # to avoid race conditions. If we were to commit the registration first, 
    # and then increment the registered_count, we could end up with a situation where
    # two users are able to register for the same session even though it is full.
    # By doing both operations in a single transaction, we ensure that the registered_count 
    # is always accurate and that no more users can register than the max_capacity allows.

    try:
        db.add(registration)
        training_session.registered_count += 1

        db.commit()
        db.refresh(registration)

    except IntegrityError:
        db.rollback()
        raise AlreadyRegisteredError

    return registration
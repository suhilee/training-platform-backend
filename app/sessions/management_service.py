from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.attendance import Attendance
from app.sessions.exceptions import (
    TrainingTypeNotFoundError,
    AgeCategoryNotFoundError,
    SessionNotFoundError,
    CapacityBelowRegistrationCountError,
    TargetAgeCategoryHasRegistrationsError,
)

from app.sessions.schemas import (
    SessionAttendeeResponse,
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionManagementListItemResponse,
)

from app.models.session_target_category import SessionTargetCategory
from app.models.age_category import AgeCategory
from app.models.registration import Registration
from app.models.user import User

from app.sessions.status import get_session_status
from app.sessions.notifications import send_session_posted_emails
from app.sessions.notifications import send_session_cancellation_emails

def create_session(
    db: Session,
    request: SessionCreateRequest,
) -> TrainingSession:
    if request.training_id is not None:
        training_type = db.get(
            TrainingType,
            request.training_id,
        )

        if training_type is None:
            raise TrainingTypeNotFoundError
    else:
        training_type = TrainingType(
            training_code=request.new_training_type.training_code,
            name=request.new_training_type.name,
            description=request.new_training_type.description,
        )

        db.add(training_type)

    for age_category_id in request.target_age_category_ids:
        age_category = db.get(
            AgeCategory,
            age_category_id,
        )

        if age_category is None:
            raise AgeCategoryNotFoundError
        
    created_session = TrainingSession(
        training_type=training_type,
        title=request.title,
        description=request.description,
        date=request.date,
        start_time=request.start_time,
        duration_minutes=request.duration_minutes,
        max_capacity=request.max_capacity,
        zoom_url=request.zoom_url,
        instructor_name=request.instructor_name,
        prerequisites=request.prerequisites,
        instructor_email=request.instructor_email,
        instructor_phone=request.instructor_phone,
    )

    for age_category_id in request.target_age_category_ids:
        created_session.target_categories.append(
            SessionTargetCategory(
                age_category_id=age_category_id,
            )
        )

    db.add(created_session)

    db.commit()
    db.refresh(created_session)

    send_session_posted_emails(
        db,
        created_session,
    )
    
    return created_session

def cancel_session(
    db: Session,
    session_id: UUID,
) -> TrainingSession:
    training_session = db.get(
        TrainingSession,
        session_id,
    )

    if training_session is None:
        raise SessionNotFoundError

    if training_session.is_cancelled:
        return training_session

    training_session.is_cancelled = True
    training_session.cancelled_at = datetime.now()

    db.commit()
    db.refresh(training_session)

    send_session_cancellation_emails(
        db,
        training_session,
    )
    
    return training_session

def update_session(
    db: Session,
    session_id: UUID,
    request: SessionUpdateRequest,
) -> TrainingSession:
    training_session = db.get(
        TrainingSession,
        session_id,
    )

    if training_session is None:
        raise SessionNotFoundError

    if request.max_capacity < training_session.registered_count:
        raise CapacityBelowRegistrationCountError
    
    current_category_ids = {
        target_category.age_category_id
        for target_category in training_session.target_categories
    }

    new_category_ids = set(request.target_age_category_ids)

    removed_category_ids = current_category_ids - new_category_ids

    if removed_category_ids:
        registered_users_statement = (
            select(User)
            .join(
                Registration,
                Registration.user_id == User.id,
            )
            .where(Registration.session_id == session_id)
        )

        registered_users = db.execute(
            registered_users_statement,
        ).scalars().all()

        if any(
            user.age_category_id in removed_category_ids
            for user in registered_users
        ):
            raise TargetAgeCategoryHasRegistrationsError
    
    for age_category_id in request.target_age_category_ids:
        age_category = db.get(
            AgeCategory,
            age_category_id,
        )

        if age_category is None:
            raise AgeCategoryNotFoundError

    training_session.target_categories = [
        SessionTargetCategory(
            age_category_id=age_category_id,
        )
        for age_category_id in request.target_age_category_ids
    ]

    training_session.title = request.title
    training_session.description = request.description
    training_session.date = request.date
    training_session.start_time = request.start_time
    training_session.duration_minutes = request.duration_minutes
    training_session.max_capacity = request.max_capacity
    training_session.zoom_url = request.zoom_url
    training_session.instructor_name = request.instructor_name
    training_session.prerequisites = request.prerequisites
    training_session.instructor_email = request.instructor_email
    training_session.instructor_phone = request.instructor_phone

    db.commit()
    db.refresh(training_session)

    return training_session

def get_session_management_detail(
    db: Session,
    session_id: UUID,
) -> tuple[TrainingSession, int, list[SessionAttendeeResponse]]:
    training_session = db.get(
        TrainingSession,
        session_id,
    )

    if training_session is None:
        raise SessionNotFoundError

    attendee_statement = (
        select(
            Registration,
            User,
            Attendance,
        )
        .join(
            User,
            Registration.user_id == User.id,
        )
        .outerjoin(
            Attendance,
            Attendance.registration_id == Registration.id,
        )
        .where(
            Registration.session_id == session_id,
        )
        .order_by(
            User.last_name,
            User.first_name,
        )
    )

    attendee_rows = db.execute(
        attendee_statement,
    ).all()

    attendees = [
        SessionAttendeeResponse(
            registration_id=registration.id,
            first_name=user.first_name,
            last_name=user.last_name,
            has_attended=attendance is not None,
            attendance_validated=(
                attendance is not None
                and attendance.validated_at is not None
            ),
        )
        for registration, user, attendance in attendee_rows
    ]

    attended_count = sum(
        attendee.has_attended
        for attendee in attendees
    )

    return training_session, attended_count, attendees

def get_managed_sessions(
    db: Session,
) -> list[SessionManagementListItemResponse]:
    sessions = (
        db.query(TrainingSession)
        .options(
            selectinload(TrainingSession.target_categories),
        )
        .order_by(TrainingSession.date, TrainingSession.start_time)
        .all()
    )

    now = datetime.now()

    return [
        SessionManagementListItemResponse(
            id=session.id,
            title=session.title,
            date=session.date,
            start_time=session.start_time,
            duration_minutes=session.duration_minutes,
            max_capacity=session.max_capacity,
            registered_count=session.registered_count,
            instructor_name=session.instructor_name,
            status=get_session_status(session, now),
            target_age_category_ids=[
                target_category.age_category_id
                for target_category in session.target_categories
            ],
        )
        for session in sessions
    ]
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.db import get_db
from app.models.user import User, UserRole
from app.registrations.schemas import (
    SessionListItemResponse,
    MySessionItemResponse,
    JoinSessionResponse,
)
from app.sessions.schemas import SessionCreateRequest, SessionCreateResponse

from app.sessions.exceptions import (
    SessionNotFoundOrIneligibleError,
    TrainingTypeNotFoundError,
    AgeCategoryNotFoundError,
    SessionNotFoundError as ManagedSessionNotFoundError,
)

from app.registrations.exceptions import (
    NotRegisteredError,
    ZoomAccessNotOpenError,
    IneligibleForSessionError,
    SessionNotFoundError,
    SessionCancelledError,
    SessionCompletedError,
)

from app.sessions.service import get_eligible_sessions, get_eligible_session_by_id
from app.sessions.status import get_session_status
from app.registrations.service import (
    get_my_sessions, 
    get_registration_state,
    join_session,
)
from app.sessions.management_service import (
    create_session,
    cancel_session,
)

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
)

@router.get(
    "",
    response_model=list[SessionListItemResponse],
)
def list_eligible_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SessionListItemResponse]:
    sessions = get_eligible_sessions(
        db=db,
        current_user=current_user,
    )
    now = datetime.now()

    status_order = {
    "open": 0,
    "running": 1,
    "full": 2,
    "completed": 3,
    "cancelled": 4,
    }

    response_items = [
        SessionListItemResponse(
            id=training_session.id,
            title=training_session.title,
            description=training_session.description,
            date=training_session.date,
            start_time=training_session.start_time,
            duration_minutes=training_session.duration_minutes,
            max_capacity=training_session.max_capacity,
            registered_count=training_session.registered_count,
            instructor_name=training_session.instructor_name,
            is_cancelled=training_session.is_cancelled,
            status=get_session_status(training_session, now),
        )
        for training_session in sessions
    ]

    return sorted(
        response_items,
        key=lambda item: (
            status_order[item.status],
            item.date,
            item.start_time,
        ),
    )


@router.get(
    "/my",
    response_model=list[MySessionItemResponse],
)
def list_my_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MySessionItemResponse]:
    my_sessions = get_my_sessions(
        db=db,
        current_user=current_user,
    )

    now = datetime.now()

    return [
        MySessionItemResponse(
            id=training_session.id,
            title=training_session.title,
            description=training_session.description,
            date=training_session.date,
            start_time=training_session.start_time,
            duration_minutes=training_session.duration_minutes,
            max_capacity=training_session.max_capacity,
            registered_count=training_session.registered_count,
            instructor_name=training_session.instructor_name,
            is_cancelled=training_session.is_cancelled,
            status=get_session_status(training_session, now),
            registration_id=registration.id,
            registration_state=get_registration_state(
                training_session,
                has_attendance,
            ),
            registered_at=registration.registered_at,
        )
        for registration, training_session, has_attendance in my_sessions
    ]


@router.get(
    "/{session_id}",
    response_model=SessionListItemResponse,
)
def get_eligible_session_detail(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionListItemResponse:
    try:
        training_session = get_eligible_session_by_id(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )
    except SessionNotFoundOrIneligibleError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    return SessionListItemResponse(
        id=training_session.id,
        title=training_session.title,
        description=training_session.description,
        date=training_session.date,
        start_time=training_session.start_time,
        duration_minutes=training_session.duration_minutes,
        max_capacity=training_session.max_capacity,
        registered_count=training_session.registered_count,
        instructor_name=training_session.instructor_name,
        is_cancelled=training_session.is_cancelled,
        status=get_session_status(
            training_session,
            datetime.now(),
        ),
    )


@router.post(
    "/{session_id}/join",
    response_model=JoinSessionResponse,
)
def join_training_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JoinSessionResponse:
    try:
        zoom_url = join_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )
    except NotRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not registered for this session.",
        )
    except ZoomAccessNotOpenError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Zoom access is not available yet.",
        )
    except IneligibleForSessionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not eligible to join this session.",
        )
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )
    except SessionCancelledError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This session has been cancelled.",
        )
    except SessionCompletedError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This session has already been completed.",
        )

    return JoinSessionResponse(
        zoom_url=zoom_url,
    )

# SESSION-MANAGER ACTIONS

@router.post(
    "",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_training_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SESSION_MANAGER),
    ),
) -> SessionCreateResponse:
    try:
        created_session = create_session(
            db=db,
            request=request,
        )
    except TrainingTypeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training type not found."
        )
    except AgeCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Age category not found.",
        )
    
    return SessionCreateResponse(
        id=created_session.id,
        training_id=created_session.training_id,
        title=created_session.title,
        description=created_session.description,
        date=created_session.date,
        start_time=created_session.start_time,
        duration_minutes=created_session.duration_minutes,
        max_capacity=created_session.max_capacity,
        registered_count=created_session.registered_count,
        instructor_name=created_session.instructor_name,
        is_cancelled=created_session.is_cancelled,
    )


@router.post(
    "/{session_id}/cancel",
)
def cancel_training_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SESSION_MANAGER),
    ),
) -> dict[str, UUID | bool]:
    try:
        cancelled_session = cancel_session(
            db=db,
            session_id=session_id,
        )
    except ManagedSessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    return {
        "id": cancelled_session.id,
        "is_cancelled": cancelled_session.is_cancelled,
    }


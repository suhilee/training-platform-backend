from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.user import User

from app.registrations.schemas import (
    RegistrationResponse,
    SessionListItemResponse,
    JoinSessionResponse,
    MySessionItemResponse,
)

from app.sessions.exceptions import SessionNotFoundOrIneligibleError
from app.sessions.service import get_eligible_sessions, get_eligible_session_by_id
from app.sessions.status import get_session_status

from app.registrations.service import (
    register_for_session,
    unregister_from_session,
    join_session,
    get_my_sessions,
    get_registration_state,
)

from app.registrations.exceptions import (
    AlreadyRegisteredError,
    IneligibleForSessionError,
    RegistrationClosedError,
    SessionCancelledError,
    SessionCompletedError,
    SessionFullError,
    SessionNotFoundError,
    NotRegisteredError,
    UnregistrationClosedError,
    ZoomAccessNotOpenError,
)


router = APIRouter(
    prefix="/sessions",
    tags=["registrations"],
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
    "/{session_id}/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RegistrationResponse:
    try:
        registration = register_for_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    except SessionFullError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This session has reached its maximum capacity.",
        )

    except AlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already registered for this session.",
        )

    except IneligibleForSessionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not eligible to register for this session.",
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

    except RegistrationClosedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration for this session is closed.",
        )

    return RegistrationResponse(
        id=registration.id,
        session_id=registration.session_id,
        registered_at=registration.registered_at,
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


@router.delete(
    "/{session_id}/register",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unregister_from_training_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        unregister_from_session(
            db=db,
            current_user=current_user,
            session_id=session_id,
        )

    except NotRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered for this session.",
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

    except UnregistrationClosedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unregistration for this session is closed.",
        )

    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request.",
        )


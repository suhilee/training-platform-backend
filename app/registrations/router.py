from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.user import User

from app.registrations.schemas import (
    RegistrationResponse,
    JoinSessionResponse,
)

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


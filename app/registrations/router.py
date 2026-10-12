from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.user import User

from app.registrations.schemas import RegistrationResponse
from app.registrations.service import register_for_session

from app.registrations.exceptions import (
    AlreadyRegisteredError,
    IneligibleForSessionError,
    RegistrationClosedError,
    SessionCancelledError,
    SessionCompletedError,
    SessionFullError,
    SessionNotFoundError,
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

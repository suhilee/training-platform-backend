from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.db import get_db
from app.models.user import User, UserRole

from app.certificates.exceptions import (
    AttendanceNotValidatedError,
    CertificateAlreadyIssuedError,
    RegistrationNotFoundError,
    CertificateNotOwnedError,
    CertificateNotFoundError,
)

from app.certificates.schemas import (
    CertificateResponse,
    CertificateDataResponse,
    CertificateListItemResponse,
)
from app.certificates.service import (
    issue_certificate,
    get_certificate_data,
    list_certificates_for_current_user,
)


router = APIRouter(
    prefix="/certificates",
    tags=["certificates"],
)


@router.post(
    "/registrations/{registration_id}",
    response_model=CertificateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_certificate(
    registration_id: UUID,
    db: Session = Depends(get_db),
    current_manager: User = Depends(
        require_role(UserRole.SESSION_MANAGER)
    ),
) -> CertificateResponse:
    try:
        certificate = issue_certificate(
            db=db,
            registration_id=registration_id,
            current_manager=current_manager,
        )
    except RegistrationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found.",
        )
    except AttendanceNotValidatedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance must be validated before issuing a certificate.",
        )
    except CertificateAlreadyIssuedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A certificate has already been issued for this registration.",
        )

    return certificate


@router.get(
    "/",
    response_model=list[CertificateListItemResponse],
)
def list_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CertificateListItemResponse]:
    return list_certificates_for_current_user(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/{registration_id}",
    response_model=CertificateDataResponse,
)
def get_certificate(
    registration_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CertificateDataResponse:
    try:
        return get_certificate_data(
            db=db,
            registration_id=registration_id,
            current_user=current_user,
        )
    except RegistrationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found.",
        )
    except CertificateNotOwnedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this certificate.",
        )
    except CertificateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found.",
        )



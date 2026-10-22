from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.certificate import Certificate
from app.models.attendance import Attendance
from app.models.user import User
from app.models.registration import Registration

from app.certificates.exceptions import (
    RegistrationNotFoundError,
    AttendanceNotValidatedError,
    CertificateAlreadyIssuedError,
)



def issue_certificate(
    db: Session,
    registration_id: UUID,
    current_manager: User,
) -> Certificate:
    registration = db.execute(
        select(Registration).where(
            Registration.id == registration_id
        )
    ).scalar_one_or_none()

    if registration is None:
        raise RegistrationNotFoundError

    attendance = db.execute(
        select(Attendance).where(
            Attendance.registration_id == registration.id
        )
    ).scalar_one_or_none()

    if attendance is None or attendance.validated_at is None:
        raise AttendanceNotValidatedError

    existing_certificate = db.execute(
        select(Certificate).where(
            Certificate.registration_id == registration.id
        )
    ).scalar_one_or_none()

    if existing_certificate is not None:
        raise CertificateAlreadyIssuedError

    certificate = Certificate(
        registration_id=registration.id,
        validated_by=current_manager.id,
    )

    try:
        db.add(certificate)
        db.commit()
        db.refresh(certificate)
    except IntegrityError:
        db.rollback()
        raise CertificateAlreadyIssuedError

    return certificate

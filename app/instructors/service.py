import logging
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.instructors.exceptions import (
    InstructorAssignedToSessionsError,
    InstructorEmailAlreadyExistsError,
    InstructorNotFoundError,
    InstructorPhotoTooLargeError,
    InvalidInstructorPhotoTypeError,
)
from app.instructors.schemas import (
    InstructorCreateRequest,
    InstructorListItemResponse,
    InstructorUpdateRequest,
    PublicInstructorListItemResponse,
)
from app.models.instructor import Instructor
from app.models.session import Session as TrainingSession


logger = logging.getLogger(__name__)

INSTRUCTOR_UPLOAD_DIR = (
    Path(__file__).resolve().parents[2] / "uploads" / "instructors"
)
INSTRUCTOR_PHOTO_URL_PREFIX = "/uploads/instructors"
MAX_INSTRUCTOR_PHOTO_SIZE = 5 * 1024 * 1024
ALLOWED_INSTRUCTOR_PHOTO_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def instructor_to_response(
    instructor: Instructor,
) -> InstructorListItemResponse:
    return InstructorListItemResponse(
        id=instructor.id,
        first_name=instructor.first_name,
        last_name=instructor.last_name,
        email=instructor.email,
        phone=instructor.phone,
        bio=instructor.bio,
        photo_url=instructor.photo_url,
        is_featured=instructor.is_featured,
    )


def list_instructors(
    db: Session,
) -> list[InstructorListItemResponse]:
    instructors = (
        db.query(Instructor)
        .order_by(
            Instructor.last_name.asc(),
            Instructor.first_name.asc(),
        )
        .all()
    )

    return [
        instructor_to_response(instructor)
        for instructor in instructors
    ]


def get_instructor(
    db: Session,
    instructor_id: UUID,
) -> Instructor:
    instructor = db.get(Instructor, instructor_id)

    if instructor is None:
        raise InstructorNotFoundError

    return instructor


def get_instructor_response(
    db: Session,
    instructor_id: UUID,
) -> InstructorListItemResponse:
    return instructor_to_response(
        get_instructor(db=db, instructor_id=instructor_id),
    )


def create_instructor(
    db: Session,
    request: InstructorCreateRequest,
) -> InstructorListItemResponse:
    email = str(request.email) if request.email is not None else None

    _ensure_email_available(db=db, email=email)

    instructor = Instructor(
        first_name=request.first_name,
        last_name=request.last_name,
        email=email,
        phone=request.phone,
        bio=request.bio,
        is_featured=request.is_featured,
    )

    db.add(instructor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise InstructorEmailAlreadyExistsError

    db.refresh(instructor)

    return instructor_to_response(instructor)


def update_instructor(
    db: Session,
    instructor_id: UUID,
    request: InstructorUpdateRequest,
) -> InstructorListItemResponse:
    instructor = get_instructor(db=db, instructor_id=instructor_id)

    email = str(request.email) if request.email is not None else None

    _ensure_email_available(
        db=db,
        email=email,
        exclude_instructor_id=instructor.id,
    )

    instructor.first_name = request.first_name
    instructor.last_name = request.last_name
    instructor.email = email
    instructor.phone = request.phone
    instructor.bio = request.bio
    instructor.is_featured = request.is_featured

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise InstructorEmailAlreadyExistsError

    db.refresh(instructor)

    return instructor_to_response(instructor)


def delete_instructor(
    db: Session,
    instructor_id: UUID,
) -> None:
    instructor = get_instructor(db=db, instructor_id=instructor_id)

    assigned_session = (
        db.query(TrainingSession.id)
        .filter(TrainingSession.instructor_id == instructor_id)
        .first()
    )

    if assigned_session is not None:
        raise InstructorAssignedToSessionsError

    photo_url = instructor.photo_url

    db.delete(instructor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise InstructorAssignedToSessionsError

    _delete_local_photo(photo_url)


def upload_instructor_photo(
    db: Session,
    instructor_id: UUID,
    content: bytes,
    content_type: str | None,
) -> InstructorListItemResponse:
    instructor = get_instructor(db=db, instructor_id=instructor_id)

    normalized_content_type = (
        content_type.split(";", 1)[0].strip().lower()
        if content_type is not None
        else None
    )

    extension = ALLOWED_INSTRUCTOR_PHOTO_TYPES.get(
        normalized_content_type,
    )

    if extension is None:
        raise InvalidInstructorPhotoTypeError

    if len(content) > MAX_INSTRUCTOR_PHOTO_SIZE:
        raise InstructorPhotoTooLargeError

    INSTRUCTOR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4()}{extension}"
    file_path = INSTRUCTOR_UPLOAD_DIR / filename

    file_path.write_bytes(content)

    old_photo_url = instructor.photo_url
    instructor.photo_url = f"{INSTRUCTOR_PHOTO_URL_PREFIX}/{filename}"

    try:
        db.commit()
    except Exception:
        db.rollback()

        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            logger.warning(
                "Failed to remove unsaved instructor photo: %s",
                file_path,
            )

        raise

    db.refresh(instructor)

    _delete_local_photo(old_photo_url)

    return instructor_to_response(instructor)


def list_public_instructors(
    db: Session,
) -> list[PublicInstructorListItemResponse]:
    instructors = (
        db.query(Instructor)
        .filter(
            Instructor.is_featured.is_(True),
            Instructor.photo_url.is_not(None),
        )
        .order_by(
            Instructor.last_name.asc(),
            Instructor.first_name.asc(),
        )
        .all()
    )

    return [
        PublicInstructorListItemResponse(
            id=instructor.id,
            first_name=instructor.first_name,
            last_name=instructor.last_name,
            bio=instructor.bio,
            photo_url=instructor.photo_url,
        )
        for instructor in instructors
    ]


def _ensure_email_available(
    db: Session,
    email: str | None,
    exclude_instructor_id: UUID | None = None,
) -> None:
    if email is None:
        return

    query = db.query(Instructor).filter(Instructor.email == email)

    if exclude_instructor_id is not None:
        query = query.filter(Instructor.id != exclude_instructor_id)

    if query.first() is not None:
        raise InstructorEmailAlreadyExistsError


def _delete_local_photo(photo_url: str | None) -> None:
    if not photo_url:
        return

    if not photo_url.startswith(f"{INSTRUCTOR_PHOTO_URL_PREFIX}/"):
        return

    filename = Path(photo_url).name

    if not filename:
        return

    file_path = INSTRUCTOR_UPLOAD_DIR / filename

    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        logger.warning(
            "Failed to remove instructor photo: %s",
            file_path,
        )

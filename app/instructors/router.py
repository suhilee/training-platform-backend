from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.db import get_db
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
from app.instructors.service import (
    MAX_INSTRUCTOR_PHOTO_SIZE,
    create_instructor,
    delete_instructor,
    get_instructor_response,
    list_instructors,
    list_public_instructors,
    update_instructor,
    upload_instructor_photo,
)
from app.models.user import User, UserRole


router = APIRouter(
    prefix="/instructors",
    tags=["instructors"],
)

public_router = APIRouter(
    prefix="/public",
    tags=["public-instructors"],
)


@router.get(
    "",
    response_model=list[InstructorListItemResponse],
)
def list_available_instructors(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SESSION_MANAGER)
    ),
) -> list[InstructorListItemResponse]:
    return list_instructors(db=db)


@router.get(
    "/{instructor_id}",
    response_model=InstructorListItemResponse,
)
def get_instructor_details(
    instructor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SESSION_MANAGER)
    ),
) -> InstructorListItemResponse:
    try:
        return get_instructor_response(
            db=db,
            instructor_id=instructor_id,
        )
    except InstructorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found.",
        )


@router.post(
    "",
    response_model=InstructorListItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_instructor_record(
    request: InstructorCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SESSION_MANAGER)
    ),
) -> InstructorListItemResponse:
    try:
        return create_instructor(db=db, request=request)
    except InstructorEmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An instructor with this email already exists.",
        )


@router.put(
    "/{instructor_id}",
    response_model=InstructorListItemResponse,
)
def update_instructor_record(
    instructor_id: UUID,
    request: InstructorUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SESSION_MANAGER)
    ),
) -> InstructorListItemResponse:
    try:
        return update_instructor(
            db=db,
            instructor_id=instructor_id,
            request=request,
        )
    except InstructorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found.",
        )
    except InstructorEmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An instructor with this email already exists.",
        )


@router.delete(
    "/{instructor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_instructor_record(
    instructor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.SESSION_MANAGER)
    ),
) -> Response:
    try:
        delete_instructor(
            db=db,
            instructor_id=instructor_id,
        )
    except InstructorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found.",
        )
    except InstructorAssignedToSessionsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This instructor is assigned to one or more sessions "
                "and cannot be deleted."
            ),
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

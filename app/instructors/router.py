from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.db import get_db
from app.models.user import User, UserRole
from app.instructors.schemas import InstructorListItemResponse
from app.instructors.service import list_instructors

router = APIRouter(
    prefix="/instructors",
    tags=["instructors"],
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

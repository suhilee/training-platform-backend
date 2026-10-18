from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.db import get_db
from app.models.user import User, UserRole
from app.training_types.schemas import TrainingTypeListItemResponse
from app.training_types.service import list_training_types

router = APIRouter(
    prefix="/training-types",
    tags=["training-types"],
)


@router.get(
    "",
    response_model=list[TrainingTypeListItemResponse],
)
def get_training_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SESSION_MANAGER)),
) -> list[TrainingTypeListItemResponse]:
    # current_user is not used in this function, but it is required to 
    # ensure that the user has the correct role to access this endpoint.
    training_types = list_training_types(db)

    return [
        TrainingTypeListItemResponse(
            id=training_type.id,
            training_code=training_type.training_code,
            name=training_type.name,
        )
        for training_type in training_types
    ]

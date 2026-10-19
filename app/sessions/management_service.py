from sqlalchemy.orm import Session

from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.sessions.exceptions import (
    TrainingTypeNotFoundError,
    AgeCategoryNotFoundError,
)

from app.sessions.schemas import SessionCreateRequest
from app.models.session_target_category import SessionTargetCategory
from app.models.age_category import AgeCategory

def create_session(
    db: Session,
    request: SessionCreateRequest,
) -> TrainingSession:
    if request.training_id is not None:
        training_type = db.get(
            TrainingType,
            request.training_id,
        )

        if training_type is None:
            raise TrainingTypeNotFoundError
    else:
        training_type = TrainingType(
            training_code=request.new_training_type.training_code,
            name=request.new_training_type.name,
            description=request.new_training_type.description,
        )

        db.add(training_type)

    for age_category_id in request.target_age_category_ids:
        age_category = db.get(
            AgeCategory,
            age_category_id,
        )

        if age_category is None:
            raise AgeCategoryNotFoundError
        
    created_session = TrainingSession(
        training_type=training_type,
        title=request.title,
        description=request.description,
        date=request.date,
        start_time=request.start_time,
        duration_minutes=request.duration_minutes,
        max_capacity=request.max_capacity,
        zoom_url=request.zoom_url,
        instructor_name=request.instructor_name,
    )

    for age_category_id in request.target_age_category_ids:
        created_session.target_categories.append(
            SessionTargetCategory(
                age_category_id=age_category_id,
            )
        )

    db.add(created_session)

    db.commit()
    db.refresh(created_session)

    return created_session

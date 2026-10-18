from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.training_type import TrainingType


def list_training_types(db: Session) -> list[TrainingType]:
    statement = select(TrainingType).order_by(TrainingType.training_code)

    return list(db.execute(statement).scalars().all())
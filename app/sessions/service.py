from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.session import Session as TrainingSession
from app.models.session_target_category import SessionTargetCategory
from app.models.user import User


def get_eligible_sessions(
    db: Session,
    current_user: User,
) -> list[TrainingSession]:
    statement = (
        select(TrainingSession)
        .join(SessionTargetCategory)
        .where(
            SessionTargetCategory.age_category_id
            == current_user.age_category_id
        )
        .options(selectinload(TrainingSession.target_categories))
    )

    return list(db.execute(statement).unique().scalars().all())


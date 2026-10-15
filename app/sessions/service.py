from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.session import Session as TrainingSession
from app.models.session_target_category import SessionTargetCategory
from app.models.user import User

from app.sessions.exceptions import SessionNotFoundOrIneligibleError

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


def get_eligible_session_by_id(
    db: Session,
    current_user: User,
    session_id: UUID,
) -> TrainingSession:
    statement = (
        select(TrainingSession)
        .join(SessionTargetCategory)
        .where(
            TrainingSession.id == session_id,
            SessionTargetCategory.age_category_id
            == current_user.age_category_id,
        )
        .options(selectinload(TrainingSession.target_categories))
    )

    training_session = db.execute(statement).unique().scalar_one_or_none()

    if training_session is None:
        raise SessionNotFoundOrIneligibleError

    return training_session

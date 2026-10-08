from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SessionTargetCategory(Base):
    __tablename__ = "session_target_categories"

    session_id: Mapped[UUID] = mapped_column(
    PostgreSQLUUID(as_uuid=True),
    ForeignKey("sessions.id"),
    primary_key=True,
    )

    age_category_id: Mapped[int] = mapped_column(
    ForeignKey("age_categories.id"),
    primary_key=True,
    )

    
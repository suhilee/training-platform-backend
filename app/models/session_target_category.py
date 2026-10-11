from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.session import Session

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

    session: Mapped["Session"] = relationship(
    back_populates="target_categories",
    )
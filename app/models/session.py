from datetime import date, datetime, time
from uuid import UUID, uuid4
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.training_type import TrainingType
from app.models.session_target_category import SessionTargetCategory

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    training_id: Mapped[UUID] = mapped_column(
        ForeignKey("training_types.id"),
        nullable=False,
        index=True,
    )

    training_type: Mapped["TrainingType"] = relationship(
    back_populates="sessions",
    )

    target_categories: Mapped[list["SessionTargetCategory"]] = relationship(
    back_populates="session",
    cascade="all, delete-orphan",
    )
    
    title: Mapped[str] = mapped_column(
    String(200),
    nullable=False,
    )

    description: Mapped[str] = mapped_column(
    Text,
    nullable=False,
    )

    date: Mapped[date] = mapped_column(
    Date,
    nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
    Time,
    nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
    Integer,
    nullable=False,
    )

    max_capacity: Mapped[int] = mapped_column(
    Integer,
    nullable=False,
    default=100,
    )

    registered_count: Mapped[int] = mapped_column(
    Integer,
    nullable=False,
    default=0,
    )

    zoom_url: Mapped[str] = mapped_column(
    String(2_000),
    nullable=False,
    )

    instructor_name: Mapped[str] = mapped_column(
    String(200),
    nullable=False,
    )

    is_cancelled: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
    )

    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
    nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now(),
    onupdate=func.now(),
    )


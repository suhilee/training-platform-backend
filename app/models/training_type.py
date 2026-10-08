from uuid import UUID, uuid4

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TrainingType(Base):
    __tablename__ = "training_types"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    training_code: Mapped[str] = mapped_column(
    String(50),
    unique=True,
    nullable=False,
    )

    name: Mapped[str] = mapped_column(
    String(100),
    unique=True,
    nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
    Text,
    nullable=True,
    )

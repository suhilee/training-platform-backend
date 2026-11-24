"""create instructors table

Revision ID: 55dc48dc0f89
Revises: 3a8678d00e78
Create Date: 2026-11-19 10:32:53.945238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '55dc48dc0f89'
down_revision: Union[str, Sequence[str], None] = '3a8678d00e78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "instructors",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "first_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "last_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "phone",
            sa.String(length=30),
            nullable=True,
        ),
        sa.Column(
            "bio",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_instructors_email"),
        "instructors",
        ["email"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
"""finalize instructor relationship on sessions

Revision ID: 1ab7fdbda5c3
Revises: f74acee7bb30
Create Date: 2026-11-24 15:56:26.629363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ab7fdbda5c3'
down_revision: Union[str, Sequence[str], None] = 'f74acee7bb30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "sessions",
        "instructor_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.drop_column("sessions", "instructor_name")
    op.drop_column("sessions", "instructor_email")
    op.drop_column("sessions", "instructor_phone")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "sessions",
        sa.Column("instructor_name", sa.String(), nullable=True),
    )
    op.add_column(
        "sessions",
        sa.Column("instructor_email", sa.String(), nullable=True),
    )
    op.add_column(
        "sessions",
        sa.Column("instructor_phone", sa.String(), nullable=True),
    )

    op.alter_column(
        "sessions",
        "instructor_id",
        existing_type=sa.UUID(),
        nullable=True,
    )

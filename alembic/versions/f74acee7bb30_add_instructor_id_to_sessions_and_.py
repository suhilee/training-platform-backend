"""add instructor_id to sessions and backfill instructors

Revision ID: f74acee7bb30
Revises: 55dc48dc0f89
Create Date: 2026-11-19 12:00:38.832524

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'f74acee7bb30'
down_revision: Union[str, Sequence[str], None] = '55dc48dc0f89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column(
            "instructor_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_sessions_instructor_id_instructors",
        "sessions",
        "instructors",
        ["instructor_id"],
        ["id"],
    )

    op.execute(
        text(
            """
            INSERT INTO instructors (
                id,
                first_name,
                last_name,
                email,
                phone,
                bio,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid(),
                split_part(s.instructor_name, ' ', 1),
                CASE
                    WHEN position(' ' IN s.instructor_name) > 0 THEN
                        trim(
                            substring(
                                s.instructor_name
                                FROM position(' ' IN s.instructor_name) + 1
                            )
                        )
                    ELSE ''
                END,
                s.instructor_email,
                s.instructor_phone,
                NULL,
                now(),
                now()
            FROM (
                SELECT DISTINCT
                    instructor_name,
                    instructor_email,
                    instructor_phone
                FROM sessions
                WHERE instructor_name IS NOT NULL
            ) AS s
            """
        )
    )

    op.execute(
        text(
            """
            UPDATE sessions
            SET instructor_id = instructors.id
            FROM instructors
            WHERE sessions.instructor_name = concat_ws(
                ' ',
                instructors.first_name,
                instructors.last_name
            )
            AND sessions.instructor_email IS NOT DISTINCT FROM instructors.email
            AND sessions.instructor_phone IS NOT DISTINCT FROM instructors.phone
            """
        )
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_sessions_instructor_id_instructors",
        "sessions",
        type_="foreignkey",
    )

    op.drop_column("sessions", "instructor_id")

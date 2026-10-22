from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


test_engine = create_engine(
    settings.test_database_url,
    pool_pre_ping=True,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = TestSessionLocal()

    try:
        yield db
    finally:
        db.close()

        with test_engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE TABLE "
                    "certificates,"
                    "attendances, "
                    "registrations, "
                    "session_target_categories, "
                    "sessions, "
                    "users, "
                    "training_types, "
                    "age_categories "
                    "RESTART IDENTITY CASCADE"
                )
            )

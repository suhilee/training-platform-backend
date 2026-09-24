from sqlalchemy import text

from app.db import SessionLocal


def test_database_connection() -> None:
    db = SessionLocal()
    try:
        database_name = db.execute(text("SELECT current_database()")).scalar()

        assert database_name == "training_platform"
    finally:
        db.close()

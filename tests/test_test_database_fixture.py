from sqlalchemy import text
from sqlalchemy.orm import Session


def test_db_session_uses_test_database(db_session: Session) -> None:
    database_name = db_session.execute(
        text("SELECT current_database()")
    ).scalar_one()

    assert database_name == "training_platform_test"
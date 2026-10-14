from types import SimpleNamespace
from unittest.mock import MagicMock

from app.sessions.service import get_eligible_sessions


def test_get_eligible_sessions_returns_query_results() -> None:
    current_user = SimpleNamespace(age_category_id=3)

    first_session = SimpleNamespace(id="first")
    second_session = SimpleNamespace(id="second")

    query_result = MagicMock()
    query_result.unique.return_value.scalars.return_value.all.return_value = [
        first_session,
        second_session,
    ]

    db = MagicMock()
    db.execute.return_value = query_result

    result = get_eligible_sessions(
        db=db,
        current_user=current_user,
    )

    assert result == [first_session, second_session]
    db.execute.assert_called_once()
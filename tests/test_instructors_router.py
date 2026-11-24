from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.instructors.schemas import InstructorListItemResponse
from app.main import app
from app.models.instructor import Instructor
from app.models.user import UserRole


def test_session_manager_can_list_instructors(monkeypatch) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)

    instructors = [
        InstructorListItemResponse(
            id=uuid4(),
            first_name="Amine",
            last_name="Benali",
        ),
        InstructorListItemResponse(
            id=uuid4(),
            first_name="Sara",
            last_name="Cherif",
        ),
    ]

    service_mock = Mock(return_value=instructors)

    monkeypatch.setattr(
        "app.instructors.router.list_instructors",
        service_mock,
    )

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.get("/instructors")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(instructors[0].id),
            "first_name": "Amine",
            "last_name": "Benali",
        },
        {
            "id": str(instructors[1].id),
            "first_name": "Sara",
            "last_name": "Cherif",
        },
    ]

    for instructor in response.json():
        assert set(instructor) == {"id", "first_name", "last_name"}

    service_mock.assert_called_once_with(db=fake_db)


def test_list_instructors_sorts_by_last_name_then_first_name(
    db_session,
) -> None:
    suffix = uuid4().hex

    db_session.add_all(
        [
            Instructor(
                first_name="Zed",
                last_name=f"{suffix}_M",
            ),
            Instructor(
                first_name="Amy",
                last_name=f"{suffix}_M",
            ),
            Instructor(
                first_name="Test",
                last_name=f"{suffix}_A",
            ),
        ]
    )
    db_session.commit()

    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: manager

    client = TestClient(app)

    try:
        response = client.get("/instructors")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    sort_keys = [
        (instructor["last_name"], instructor["first_name"])
        for instructor in body
    ]

    assert sort_keys == sorted(sort_keys)

    matching_instructors = [
        (instructor["last_name"], instructor["first_name"])
        for instructor in body
        if instructor["last_name"].startswith(suffix)
    ]

    assert matching_instructors == [
        (f"{suffix}_A", "Test"),
        (f"{suffix}_M", "Amy"),
        (f"{suffix}_M", "Zed"),
    ]


def test_participant_cannot_list_instructors() -> None:
    participant = SimpleNamespace(role=UserRole.PARTICIPANT)

    app.dependency_overrides[get_current_user] = lambda: participant

    client = TestClient(app)

    try:
        response = client.get("/instructors")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to perform this action.",
    }


def test_unauthenticated_user_cannot_list_instructors() -> None:
    client = TestClient(app)

    response = client.get("/instructors")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }
    assert response.headers["www-authenticate"] == "Bearer"

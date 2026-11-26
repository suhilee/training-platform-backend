from datetime import date, time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.instructors.schemas import InstructorListItemResponse
from app.main import app
from app.models.instructor import Instructor
from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType
from app.models.user import UserRole


def override_manager_dependencies(db_session) -> None:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        role=UserRole.SESSION_MANAGER,
    )


def test_session_manager_can_list_instructors(monkeypatch) -> None:
    fake_db = object()
    manager = SimpleNamespace(role=UserRole.SESSION_MANAGER)

    instructors = [
        InstructorListItemResponse(
            id=uuid4(),
            first_name="Amine",
            last_name="Benali",
            email="amine@example.com",
            phone="0555123456",
            bio="Experienced trainer",
            photo_url="/uploads/instructors/amine.jpg",
            is_featured=True,
        ),
        InstructorListItemResponse(
            id=uuid4(),
            first_name="Sara",
            last_name="Cherif",
            email=None,
            phone=None,
            bio=None,
            photo_url=None,
            is_featured=False,
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
            "email": "amine@example.com",
            "phone": "0555123456",
            "bio": "Experienced trainer",
            "photo_url": "/uploads/instructors/amine.jpg",
            "is_featured": True,
        },
        {
            "id": str(instructors[1].id),
            "first_name": "Sara",
            "last_name": "Cherif",
            "email": None,
            "phone": None,
            "bio": None,
            "photo_url": None,
            "is_featured": False,
        },
    ]

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

    override_manager_dependencies(db_session)

    client = TestClient(app)

    try:
        response = client.get("/instructors")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

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


def test_manager_can_create_instructor_with_required_fields(
    db_session,
) -> None:
    override_manager_dependencies(db_session)

    client = TestClient(app)

    try:
        response = client.post(
            "/instructors",
            json={
                "first_name": "Amine",
                "last_name": "Benali",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    body = response.json()

    assert body["first_name"] == "Amine"
    assert body["last_name"] == "Benali"
    assert body["email"] is None
    assert body["phone"] is None
    assert body["bio"] is None
    assert body["photo_url"] is None
    assert body["is_featured"] is False


def test_manager_can_create_instructor_with_all_optional_fields(
    db_session,
) -> None:
    email = f"instructor-{uuid4().hex}@example.com"

    override_manager_dependencies(db_session)

    client = TestClient(app)

    try:
        response = client.post(
            "/instructors",
            json={
                "first_name": "Amine",
                "last_name": "Benali",
                "email": email,
                "phone": "0555123456",
                "bio": "Experienced trainer",
                "is_featured": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == email
    assert body["phone"] == "0555123456"
    assert body["bio"] == "Experienced trainer"
    assert body["is_featured"] is True


def test_create_instructor_rejects_duplicate_email(
    db_session,
) -> None:
    email = f"duplicate-{uuid4().hex}@example.com"

    override_manager_dependencies(db_session)

    client = TestClient(app)

    try:
        first_response = client.post(
            "/instructors",
            json={
                "first_name": "First",
                "last_name": "Instructor",
                "email": email,
            },
        )
        second_response = client.post(
            "/instructors",
            json={
                "first_name": "Second",
                "last_name": "Instructor",
                "email": email,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "An instructor with this email already exists."
    )


def test_manager_can_get_instructor_details(db_session) -> None:
    email = f"detail-{uuid4().hex}@example.com"

    instructor = Instructor(
        first_name="Detail",
        last_name="Instructor",
        email=email,
        phone="0555000000",
        bio="Instructor bio",
        is_featured=True,
    )

    db_session.add(instructor)
    db_session.commit()

    override_manager_dependencies(db_session)

    client = TestClient(app)

    try:
        response = client.get(f"/instructors/{instructor.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": str(instructor.id),
        "first_name": "Detail",
        "last_name": "Instructor",
        "email": email,
        "phone": "0555000000",
        "bio": "Instructor bio",
        "photo_url": None,
        "is_featured": True,
    }


def test_manager_can_clear_optional_fields_and_unfeature_instructor(
    db_session,
) -> None:
    email = f"update-{uuid4().hex}@example.com"

    instructor = Instructor(
        first_name="Old",
        last_name="Name",
        email=email,
        phone="0555111111",
        bio="Old bio",
        is_featured=True,
    )

    db_session.add(instructor)
    db_session.commit()

    override_manager_dependencies(db_session)

    client = TestClient(app)

    try:
        response = client.put(
            f"/instructors/{instructor.id}",
            json={
                "first_name": "New",
                "last_name": "Name",
                "email": None,
                "phone": None,
                "bio": None,
                "is_featured": False,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["first_name"] == "New"
    assert body["last_name"] == "Name"
    assert body["email"] is None
    assert body["phone"] is None
    assert body["bio"] is None
    assert body["is_featured"] is False


def test_manager_can_feature_and_unfeature_instructor(db_session) -> None:
    instructor = Instructor(
        first_name="Feature",
        last_name="Instructor",
        is_featured=False,
    )

    db_session.add(instructor)
    db_session.commit()

    override_manager_dependencies(db_session)

    client = TestClient(app)

    try:
        featured_response = client.put(
            f"/instructors/{instructor.id}",
            json={
                "first_name": "Feature",
                "last_name": "Instructor",
                "is_featured": True,
            },
        )
        unfeatured_response = client.put(
            f"/instructors/{instructor.id}",
            json={
                "first_name": "Feature",
                "last_name": "Instructor",
                "is_featured": False,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert featured_response.status_code == 200
    assert featured_response.json()["is_featured"] is True
    assert unfeatured_response.status_code == 200
    assert unfeatured_response.json()["is_featured"] is False


def test_manager_can_delete_unassigned_instructor(db_session) -> None:
    instructor = Instructor(
        first_name="Delete",
        last_name="Instructor",
    )

    db_session.add(instructor)
    db_session.commit()

    instructor_id = instructor.id

    override_manager_dependencies(db_session)

    client = TestClient(app)

    try:
        response = client.delete(f"/instructors/{instructor_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert db_session.get(Instructor, instructor_id) is None


def test_manager_cannot_delete_instructor_assigned_to_session(
    db_session,
) -> None:
    instructor = Instructor(
        first_name="Assigned",
        last_name="Instructor",
    )

    training_type = TrainingType(
        training_code=f"ASSIGNED-{uuid4().hex}",
        name="Assigned Instructor Training",
    )

    db_session.add_all([instructor, training_type])
    db_session.flush()

    training_session = TrainingSession(
        training_id=training_type.id,
        title="Assigned session",
        description="A session assigned to an instructor.",
        date=date(2030, 1, 1),
        start_time=time(10, 0),
        duration_minutes=60,
        max_capacity=10,
        zoom_url="https://example.com/assigned",
        instructor_id=instructor.id,
    )

    db_session.add(training_session)
    db_session.commit()

    override_manager_dependencies(db_session)

    client = TestClient(app)

    try:
        response = client.delete(f"/instructors/{instructor.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "This instructor is assigned to one or more sessions "
        "and cannot be deleted."
    )
    assert db_session.get(Instructor, instructor.id) is not None


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


def test_participant_cannot_create_instructor() -> None:
    participant = SimpleNamespace(role=UserRole.PARTICIPANT)

    app.dependency_overrides[get_current_user] = lambda: participant

    client = TestClient(app)

    try:
        response = client.post(
            "/instructors",
            json={
                "first_name": "Blocked",
                "last_name": "Instructor",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_unauthenticated_user_cannot_list_instructors() -> None:
    client = TestClient(app)

    response = client.get("/instructors")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_missing_instructor_returns_404(db_session) -> None:
    override_manager_dependencies(db_session)

    client = TestClient(app)

    try:
        response = client.get(f"/instructors/{uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Instructor not found."

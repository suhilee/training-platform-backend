from datetime import date, time
from pathlib import Path
from uuid import uuid4

import pytest

from app.instructors.exceptions import (
    InstructorAssignedToSessionsError,
    InstructorEmailAlreadyExistsError,
    InstructorNotFoundError,
    InstructorPhotoTooLargeError,
    InvalidInstructorPhotoTypeError,
)
from app.instructors.schemas import (
    InstructorCreateRequest,
    InstructorUpdateRequest,
)
from app.instructors.service import (
    MAX_INSTRUCTOR_PHOTO_SIZE,
    create_instructor,
    delete_instructor,
    get_instructor_response,
    list_public_instructors,
    update_instructor,
    upload_instructor_photo,
)
from app.models.instructor import Instructor
from app.models.session import Session as TrainingSession
from app.models.training_type import TrainingType


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def test_create_instructor_with_required_fields(db_session) -> None:
    result = create_instructor(
        db=db_session,
        request=InstructorCreateRequest(
            first_name="Amine",
            last_name="Benali",
        ),
    )

    assert result.id is not None
    assert result.first_name == "Amine"
    assert result.last_name == "Benali"
    assert result.email is None
    assert result.phone is None
    assert result.bio is None
    assert result.photo_url is None
    assert result.is_featured is False


def test_create_instructor_with_all_optional_fields(db_session) -> None:
    email = unique_email("create-all")

    result = create_instructor(
        db=db_session,
        request=InstructorCreateRequest(
            first_name="Amine",
            last_name="Benali",
            email=email,
            phone="0555123456",
            bio="Experienced trainer",
            is_featured=True,
        ),
    )

    assert result.email == email
    assert result.phone == "0555123456"
    assert result.bio == "Experienced trainer"
    assert result.is_featured is True


def test_create_instructor_rejects_duplicate_email(db_session) -> None:
    email = unique_email("duplicate")

    create_instructor(
        db=db_session,
        request=InstructorCreateRequest(
            first_name="First",
            last_name="Instructor",
            email=email,
        ),
    )

    with pytest.raises(InstructorEmailAlreadyExistsError):
        create_instructor(
            db=db_session,
            request=InstructorCreateRequest(
                first_name="Second",
                last_name="Instructor",
                email=email,
            ),
        )


def test_get_instructor_response_returns_instructor(db_session) -> None:
    instructor = Instructor(
        first_name="Detail",
        last_name="Instructor",
        email=unique_email("detail"),
        phone="0555000000",
        bio="Instructor bio",
        is_featured=True,
    )

    db_session.add(instructor)
    db_session.commit()

    result = get_instructor_response(
        db=db_session,
        instructor_id=instructor.id,
    )

    assert result.id == instructor.id
    assert result.first_name == "Detail"
    assert result.last_name == "Instructor"
    assert result.email == instructor.email
    assert result.phone == "0555000000"
    assert result.bio == "Instructor bio"
    assert result.is_featured is True


def test_update_instructor_updates_fields(db_session) -> None:
    instructor = Instructor(
        first_name="Old",
        last_name="Name",
        email=unique_email("old"),
        phone="0555111111",
        bio="Old bio",
        is_featured=False,
    )

    db_session.add(instructor)
    db_session.commit()

    email = unique_email("new")

    result = update_instructor(
        db=db_session,
        instructor_id=instructor.id,
        request=InstructorUpdateRequest(
            first_name="New",
            last_name="Name",
            email=email,
            phone="0555222222",
            bio="New bio",
            is_featured=True,
        ),
    )

    assert result.first_name == "New"
    assert result.last_name == "Name"
    assert result.email == email
    assert result.phone == "0555222222"
    assert result.bio == "New bio"
    assert result.is_featured is True


def test_update_instructor_clears_optional_fields(db_session) -> None:
    instructor = Instructor(
        first_name="Clear",
        last_name="Fields",
        email=unique_email("clear"),
        phone="0555333333",
        bio="Bio to clear",
        is_featured=True,
    )

    db_session.add(instructor)
    db_session.commit()

    result = update_instructor(
        db=db_session,
        instructor_id=instructor.id,
        request=InstructorUpdateRequest(
            first_name="Clear",
            last_name="Fields",
            email=None,
            phone=None,
            bio=None,
            is_featured=False,
        ),
    )

    assert result.email is None
    assert result.phone is None
    assert result.bio is None
    assert result.is_featured is False


def test_update_instructor_rejects_email_owned_by_another(
    db_session,
) -> None:
    first_instructor = Instructor(
        first_name="First",
        last_name="Instructor",
        email=unique_email("first"),
    )

    second_instructor = Instructor(
        first_name="Second",
        last_name="Instructor",
        email=unique_email("second"),
    )

    db_session.add_all([first_instructor, second_instructor])
    db_session.commit()

    with pytest.raises(InstructorEmailAlreadyExistsError):
        update_instructor(
            db=db_session,
            instructor_id=second_instructor.id,
            request=InstructorUpdateRequest(
                first_name="Second",
                last_name="Instructor",
                email=first_instructor.email,
                is_featured=False,
            ),
        )


def test_delete_instructor_removes_unassigned_instructor(
    db_session,
) -> None:
    instructor = Instructor(
        first_name="Delete",
        last_name="Instructor",
    )

    db_session.add(instructor)
    db_session.commit()

    instructor_id = instructor.id

    delete_instructor(db=db_session, instructor_id=instructor_id)

    assert db_session.get(Instructor, instructor_id) is None


def test_delete_instructor_rejects_assigned_instructor(
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

    with pytest.raises(InstructorAssignedToSessionsError):
        delete_instructor(
            db=db_session,
            instructor_id=instructor.id,
        )

    assert db_session.get(Instructor, instructor.id) is not None


def test_delete_instructor_removes_local_photo(
    db_session,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.instructors.service.INSTRUCTOR_UPLOAD_DIR",
        tmp_path,
    )

    instructor = Instructor(
        first_name="Photo",
        last_name="Delete",
    )

    db_session.add(instructor)
    db_session.commit()

    result = upload_instructor_photo(
        db=db_session,
        instructor_id=instructor.id,
        content=b"fake-jpeg-content",
        content_type="image/jpeg",
    )

    saved_file = tmp_path / Path(result.photo_url).name
    assert saved_file.exists()

    delete_instructor(db=db_session, instructor_id=instructor.id)

    assert not saved_file.exists()


def test_public_instructors_are_filtered_and_sorted(db_session) -> None:
    db_session.query(Instructor).update(
        {Instructor.is_featured: False},
        synchronize_session=False,
    )
    db_session.commit()

    suffix = uuid4().hex

    first_instructor = Instructor(
        first_name="Amy",
        last_name=f"{suffix}_B",
        bio="First public bio",
        photo_url="/uploads/instructors/first.jpg",
        is_featured=True,
    )

    second_instructor = Instructor(
        first_name="Zed",
        last_name=f"{suffix}_A",
        photo_url="/uploads/instructors/second.jpg",
        is_featured=True,
    )

    featured_without_photo = Instructor(
        first_name="No",
        last_name=f"{suffix}_A",
        is_featured=True,
    )

    unfeatured_with_photo = Instructor(
        first_name="Hidden",
        last_name=f"{suffix}_A",
        photo_url="/uploads/instructors/hidden.jpg",
        is_featured=False,
    )

    db_session.add_all(
        [
            first_instructor,
            second_instructor,
            featured_without_photo,
            unfeatured_with_photo,
        ]
    )
    db_session.commit()

    result = list_public_instructors(db=db_session)

    assert [instructor.id for instructor in result] == [
        second_instructor.id,
        first_instructor.id,
    ]

    assert result[0].first_name == "Zed"
    assert result[0].last_name == f"{suffix}_A"
    assert result[1].first_name == "Amy"
    assert result[1].last_name == f"{suffix}_B"
    assert result[1].bio == "First public bio"

    db_session.delete(first_instructor)
    db_session.delete(second_instructor)
    db_session.delete(featured_without_photo)
    db_session.delete(unfeatured_with_photo)
    db_session.commit()


def test_public_instructors_do_not_expose_contacts(db_session) -> None:
    db_session.query(Instructor).update(
        {Instructor.is_featured: False},
        synchronize_session=False,
    )
    db_session.commit()

    instructor = Instructor(
        first_name="Public",
        last_name="Contact",
        email=unique_email("public-contact"),
        phone="0555999999",
        photo_url="/uploads/instructors/contact.jpg",
        is_featured=True,
    )

    db_session.add(instructor)
    db_session.commit()

    result = list_public_instructors(db=db_session)

    assert len(result) == 1
    assert set(result[0].model_dump()) == {
        "id",
        "first_name",
        "last_name",
        "bio",
        "photo_url",
    }

    db_session.delete(instructor)
    db_session.commit()


def test_upload_photo_and_replace_existing(
    db_session,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.instructors.service.INSTRUCTOR_UPLOAD_DIR",
        tmp_path,
    )

    instructor = Instructor(
        first_name="Photo",
        last_name="Instructor",
    )

    db_session.add(instructor)
    db_session.commit()

    first_result = upload_instructor_photo(
        db=db_session,
        instructor_id=instructor.id,
        content=b"first-image",
        content_type="image/jpeg",
    )

    first_file = tmp_path / Path(first_result.photo_url).name
    assert first_file.exists()
    assert first_result.photo_url.endswith(".jpg")

    second_result = upload_instructor_photo(
        db=db_session,
        instructor_id=instructor.id,
        content=b"second-image",
        content_type="image/png",
    )

    second_file = tmp_path / Path(second_result.photo_url).name

    assert second_result.photo_url != first_result.photo_url
    assert second_result.photo_url.endswith(".png")
    assert second_file.exists()
    assert second_file.read_bytes() == b"second-image"
    assert not first_file.exists()


def test_upload_photo_rejects_unsupported_mime_type(
    db_session,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.instructors.service.INSTRUCTOR_UPLOAD_DIR",
        tmp_path,
    )

    instructor = Instructor(
        first_name="Bad",
        last_name="Photo",
    )

    db_session.add(instructor)
    db_session.commit()

    with pytest.raises(InvalidInstructorPhotoTypeError):
        upload_instructor_photo(
            db=db_session,
            instructor_id=instructor.id,
            content=b"fake-gif-content",
            content_type="image/gif",
        )

    assert list(tmp_path.iterdir()) == []


def test_upload_photo_rejects_too_large_file(
    db_session,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.instructors.service.INSTRUCTOR_UPLOAD_DIR",
        tmp_path,
    )

    instructor = Instructor(
        first_name="Large",
        last_name="Photo",
    )

    db_session.add(instructor)
    db_session.commit()

    with pytest.raises(InstructorPhotoTooLargeError):
        upload_instructor_photo(
            db=db_session,
            instructor_id=instructor.id,
            content=b"x" * (MAX_INSTRUCTOR_PHOTO_SIZE + 1),
            content_type="image/jpeg",
        )

    assert list(tmp_path.iterdir()) == []


def test_missing_instructor_raises_for_instructor_operations(
    db_session,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.instructors.service.INSTRUCTOR_UPLOAD_DIR",
        tmp_path,
    )

    instructor_id = uuid4()

    with pytest.raises(InstructorNotFoundError):
        get_instructor_response(
            db=db_session,
            instructor_id=instructor_id,
        )

    with pytest.raises(InstructorNotFoundError):
        update_instructor(
            db=db_session,
            instructor_id=instructor_id,
            request=InstructorUpdateRequest(
                first_name="Missing",
                last_name="Instructor",
                is_featured=False,
            ),
        )

    with pytest.raises(InstructorNotFoundError):
        delete_instructor(
            db=db_session,
            instructor_id=instructor_id,
        )

    with pytest.raises(InstructorNotFoundError):
        upload_instructor_photo(
            db=db_session,
            instructor_id=instructor_id,
            content=b"fake-image",
            content_type="image/jpeg",
        )

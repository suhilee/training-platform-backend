from sqlalchemy.orm import Session

from app.instructors.schemas import InstructorListItemResponse
from app.models.instructor import Instructor


def list_instructors(
    db: Session,
) -> list[InstructorListItemResponse]:
    instructors = (
        db.query(Instructor)
        .order_by(
            Instructor.last_name.asc(),
            Instructor.first_name.asc(),
        )
        .all()
    )

    return [
        InstructorListItemResponse(
            id=instructor.id,
            first_name=instructor.first_name,
            last_name=instructor.last_name,
        )
        for instructor in instructors
    ]

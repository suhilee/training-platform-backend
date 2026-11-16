from datetime import date, time, timedelta

from app.db import SessionLocal
from app.models.age_category import AgeCategory
from app.models.session import Session as TrainingSession
from app.models.session_target_category import SessionTargetCategory
from app.models.training_type import TrainingType


TRAINING_CODE = "MOCK-TRAINING-001"


def create_session(
    db,
    training_type,
    category,
    title,
    session_date,
    max_capacity,
    registered_count,
):
    session = TrainingSession(
        training_type=training_type,
        title=title,
        description="Mock session for local testing.",
        date=session_date,
        start_time=time(10, 0),
        duration_minutes=90,
        max_capacity=max_capacity,
        registered_count=registered_count,
        zoom_url="https://example.com/mock-zoom",
        instructor_name="Mock Instructor",
    )

    db.add(session)
    db.flush()

    db.add(
        SessionTargetCategory(
            session_id=session.id,
            age_category_id=category.id,
        )
    )

    return session


def main() -> None:
    db = SessionLocal()

    try:
        training_type = (
            db.query(TrainingType)
            .filter(
                TrainingType.training_code == TRAINING_CODE
            )
            .first()
        )

        if training_type is None:
            training_type = TrainingType(
                training_code=TRAINING_CODE,
                name="Mock Training",
                description=(
                    "Mock training used for local testing."
                ),
            )

            db.add(training_type)
            db.commit()
            db.refresh(training_type)

        categories = (
            db.query(AgeCategory)
            .order_by(AgeCategory.id)
            .all()
        )

        if not categories:
            raise RuntimeError("No age categories found.")

        future_date = date.today() + timedelta(days=7)
        past_date = date.today() - timedelta(days=7)

        created_count = 0

        for category in categories:
            full_title = (
                f"Mock Training Full - {category.code}"
            )
            one_seat_title = (
                f"Mock Training One Seat Left - "
                f"{category.code}"
            )
            completed_title = (
                f"Mock Training Completed - "
                f"{category.code}"
            )

            existing_titles = [
                row[0]
                for row in db.query(
                    TrainingSession.title
                )
                .filter(
                    TrainingSession.title.in_(
                        [
                            full_title,
                            one_seat_title,
                            completed_title,
                        ]
                    )
                )
                .all()
            ]

            if full_title not in existing_titles:
                create_session(
                    db,
                    training_type,
                    category,
                    full_title,
                    future_date,
                    max_capacity=1,
                    registered_count=1,
                )
                created_count += 1

            if one_seat_title not in existing_titles:
                create_session(
                    db,
                    training_type,
                    category,
                    one_seat_title,
                    future_date + timedelta(days=1),
                    max_capacity=2,
                    registered_count=1,
                )
                created_count += 1

            if completed_title not in existing_titles:
                create_session(
                    db,
                    training_type,
                    category,
                    completed_title,
                    past_date,
                    max_capacity=100,
                    registered_count=0,
                )
                created_count += 1

        db.commit()

        print(f"Created {created_count} mock sessions.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
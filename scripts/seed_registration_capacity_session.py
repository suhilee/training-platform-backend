from datetime import date, time, timedelta

from app.db import SessionLocal
from app.models.age_category import AgeCategory
from app.models.session import Session as TrainingSession
from app.models.session_target_category import SessionTargetCategory
from app.models.training_type import TrainingType


def main():
    db = SessionLocal()

    try:
        training_type = (
            db.query(TrainingType)
            .filter(TrainingType.name == "Registration Capacity Test")
            .first()
        )

        if training_type is None:
            training_type = TrainingType(
                training_code="RCT",
                name="Registration Capacity Test",
                description=(
                    "Training type used for registration "
                    "capacity load testing."
                ),
            )

            db.add(training_type)
            db.commit()
            db.refresh(training_type)

        age_category = (
            db.query(AgeCategory)
            .filter(AgeCategory.code == "AD")
            .first()
        )

        if age_category is None:
            raise RuntimeError(
                "Age category AD was not found. "
                "Run the user seed script first."
            )

        session_date = date.today() + timedelta(days=14)

        training_session = TrainingSession(
            training_id=training_type.id,
            title="Registration Capacity Test Session",
            description=(
                "Fresh session used to test concurrent "
                "registration capacity."
            ),
            date=session_date,
            start_time=time(10, 0),
            duration_minutes=60,
            max_capacity=100,
            registered_count=0,
            zoom_url="https://zoom.example.com/capacity-test",
            instructor_name="Capacity Test Instructor",
            is_cancelled=False,
        )

        db.add(training_session)
        db.commit()
        db.refresh(training_session)

        session_target_category = SessionTargetCategory(
            session=training_session,
            age_category_id=age_category.id,
        )

        db.add(session_target_category)
        db.commit()

        print("Session ID:")
        print(training_session.id)
        print("Capacity:")
        print(training_session.max_capacity)

    finally:
        db.close()


if __name__ == "__main__":
    main()
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
            .filter(TrainingType.name == "Load Test Training")
            .first()
        )

        if training_type is None:
            training_type = TrainingType(
                name="Load Test Training",
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

        session_date = date.today() + timedelta(days=7)

        existing_session = (
            db.query(TrainingSession)
            .filter(
                TrainingSession.title == "Load Test Session",
                TrainingSession.date == session_date,
            )
            .first()
        )

        if existing_session is not None:
            print(f"Session already exists: {existing_session.id}")
            return

        training_session = TrainingSession(
            training_id=training_type.id,
            title="Load Test Session",
            description="Session used for Locust load testing.",
            date=session_date,
            start_time=time(10, 0),
            duration_minutes=60,
            max_capacity=1000,
            registered_count=0,
            zoom_url="https://zoom.example.com/load-test",
            instructor_name="Load Test Instructor",
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

        print(f"Seeded session: {training_session.id}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
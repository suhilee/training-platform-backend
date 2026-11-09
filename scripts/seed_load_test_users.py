from datetime import date

from app.auth.password import hash_password
from app.db import SessionLocal
from app.models.age_category import AgeCategory
from app.models.user import User, UserRole


NUMBER_OF_USERS = 100
PASSWORD = "StrongPassword123"


def main() -> None:
    db = SessionLocal()

    try:
        age_category = (
            db.query(AgeCategory)
            .first()
        )

        if age_category is None:
            age_category = AgeCategory(
                code="AD",
                min_age=18,
                max_age=59,
            )

            db.add(age_category)
            db.commit()
            db.refresh(age_category)

            print("Seeded age category: AD")

        created_count = 0

        for number in range(1, NUMBER_OF_USERS + 1):
            email = f"loadtest{number}@example.com"

            existing_user = (
                db.query(User)
                .filter(User.email == email)
                .first()
            )

            if existing_user is not None:
                print(f"Skipping existing user: {email}")
                continue

            user = User(
                first_name="Load",
                last_name=f"Test {number}",
                email=email,
                phone_number=f"055000{number:04d}",
                date_of_birth=date(2000, 1, 1),
                wilaya="Alger",
                password_hash=hash_password(PASSWORD),
                age_category_id=age_category.id,
                role=UserRole.PARTICIPANT,
                email_verified=True,
            )

            db.add(user)
            created_count += 1

        db.commit()

        print(f"Created {created_count} load-test users.")
        print(f"Using age category: {age_category.code}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
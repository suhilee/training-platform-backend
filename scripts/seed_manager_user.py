import os
from datetime import date

from app.auth.password import hash_password
from app.db import SessionLocal
from app.models.age_category import AgeCategory
from app.models.user import User, UserRole


MANAGER_EMAIL = os.getenv(
    "MANAGER_EMAIL",
    "manager@example.com",
)

MANAGER_PASSWORD = os.getenv(
    "MANAGER_PASSWORD",
    "StrongManagerPassword123",
)


def main() -> None:
    db = SessionLocal()

    try:
        existing_manager = (
            db.query(User)
            .filter(User.email == MANAGER_EMAIL)
            .first()
        )

        if existing_manager is not None:
            print(f"Manager already exists: {MANAGER_EMAIL}")
            return

        age_category = (
            db.query(AgeCategory)
            .order_by(AgeCategory.id)
            .first()
        )

        if age_category is None:
            raise RuntimeError(
                "No age category found. Seed age categories first."
            )

        manager = User(
            first_name="Session",
            last_name="Manager",
            email=MANAGER_EMAIL,
            phone_number="0550000000",
            date_of_birth=date(1990, 1, 1),
            age_category_id=age_category.id,
            wilaya="Alger",
            password_hash=hash_password(MANAGER_PASSWORD),
            role=UserRole.SESSION_MANAGER,
            email_verified=True,
        )

        db.add(manager)
        db.commit()

        print(f"Created manager: {MANAGER_EMAIL}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
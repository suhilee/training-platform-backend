from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.age_category import AgeCategory


def calculate_age(date_of_birth: date) -> int:
    today = date.today()

    return today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


def get_age_category_for_date_of_birth(
    db: Session,
    date_of_birth: date,
) -> AgeCategory | None:
    age = calculate_age(date_of_birth)

    statement = select(AgeCategory).where(
        AgeCategory.min_age <= age,
        AgeCategory.max_age >= age,
    )

    return db.execute(statement).scalar_one_or_none()
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.age_category import AgeCategory

from app.auth.schemas import RegisterRequest
from app.models.user import User

from app.auth.password import hash_password

from sqlalchemy.exc import IntegrityError

def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.execute(statement).scalar_one_or_none()

def create_participant(db: Session, registration: RegisterRequest, age_category: AgeCategory) -> User:
    user = User(
    first_name=registration.first_name,
    last_name=registration.last_name,
    email=registration.email,
    phone_number=registration.phone_number,
    date_of_birth=registration.date_of_birth,
    age_category_id=age_category.id,
    wilaya=registration.wilaya,
    password_hash=hash_password(registration.password),
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(user)

    return user
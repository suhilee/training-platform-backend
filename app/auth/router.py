from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.age_categories import get_age_category_for_date_of_birth
from app.auth.password import hash_password, verify_password
from app.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    CurrentUserResponse,
    ProfileUpdateRequest,
    ChangePasswordRequest,
    )

from app.auth.service import create_participant, get_user_by_email
from app.auth.tokens import create_access_token
from app.db import get_db

from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = get_user_by_email(db, credentials.email)

    if user is None or not verify_password(
        credentials.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(access_token=create_access_token(user.id))

@router.get("/me", response_model=CurrentUserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        phone_number=current_user.phone_number,
        date_of_birth=current_user.date_of_birth,
        age_category_id=current_user.age_category_id,
        wilaya=current_user.wilaya,
        role=current_user.role,
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    registration: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    existing_user = get_user_by_email(db, registration.email)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    age_category = get_age_category_for_date_of_birth(
        db,
        registration.date_of_birth,
    )

    if age_category is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Age is not eligible for registration",
        )

    try:
        user = create_participant(db, registration, age_category)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    return RegisterResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        date_of_birth=user.date_of_birth,
        age_category_id=user.age_category_id,
        wilaya=user.wilaya,
        role=user.role,
    )


@router.patch("/me", response_model=CurrentUserResponse)
def update_current_user(
    profile_update: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentUserResponse:
    if profile_update.email is not None:
        existing_user = get_user_by_email(db, profile_update.email)

        if existing_user is not None and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

    if profile_update.date_of_birth is not None:
        age_category = get_age_category_for_date_of_birth(
            db,
            profile_update.date_of_birth,
        )

        if age_category is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Age is not eligible for registration",
            )

        current_user.date_of_birth = profile_update.date_of_birth
        current_user.age_category_id = age_category.id

    for field, value in profile_update.model_dump(
        exclude_unset=True,
        exclude={"date_of_birth"},
    ).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return CurrentUserResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        phone_number=current_user.phone_number,
        date_of_birth=current_user.date_of_birth,
        age_category_id=current_user.age_category_id,
        wilaya=current_user.wilaya,
        role=current_user.role,
    )

@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    password_change: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not verify_password(
        password_change.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    current_user.password_hash = hash_password(password_change.new_password)
    db.commit()
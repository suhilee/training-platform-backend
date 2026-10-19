from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class NewTrainingTypeInput(BaseModel):
    training_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class SessionCreateRequest(BaseModel):
    training_id: UUID | None = None
    new_training_type: NewTrainingTypeInput | None = None

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    date: date
    start_time: time
    duration_minutes: int = Field(gt=0)
    max_capacity: int = Field(default=100, gt=0)
    zoom_url: str = Field(min_length=1, max_length=2_000)
    instructor_name: str = Field(min_length=1, max_length=200)
    target_age_category_ids: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_training_type_choice(self) -> "SessionCreateRequest":
        has_existing_training = self.training_id is not None
        has_new_training = self.new_training_type is not None

        if has_existing_training == has_new_training:
            raise ValueError(
                "Provide exactly one of training_id or new_training_type."
            )

        return self

    @model_validator(mode="after")
    def validate_unique_target_age_categories(
        self,
    ) -> "SessionCreateRequest":
        if len(self.target_age_category_ids) != len(
            set(self.target_age_category_ids)
        ):
            raise ValueError(
                "Target age category IDs must be unique."
            )

        return self


class SessionCreateResponse(BaseModel):
    id: UUID
    training_id: UUID
    title: str
    description: str
    date: date
    start_time: time
    duration_minutes: int
    max_capacity: int
    registered_count: int
    instructor_name: str
    is_cancelled: bool

class SessionUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    date: date
    start_time: time
    duration_minutes: int = Field(gt=0)
    max_capacity: int = Field(gt=0)
    zoom_url: str = Field(min_length=1, max_length=2_000)
    instructor_name: str = Field(min_length=1, max_length=200)
    target_age_category_ids: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_target_age_categories(
        self,
    ) -> "SessionUpdateRequest":
        if len(self.target_age_category_ids) != len(
            set(self.target_age_category_ids)
        ):
            raise ValueError(
                "Target age category IDs must be unique."
            )

        return self
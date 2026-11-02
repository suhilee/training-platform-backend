from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.user import User
from app.notifications.email import ConsoleEmailSender, EmailMessage


def send_session_posted_emails(
    db: Session,
    training_session: TrainingSession,
) -> None:
    target_age_category_ids = [
        target_category.age_category_id
        for target_category in training_session.target_categories
    ]

    users = db.execute(
        select(User).where(
            User.age_category_id.in_(target_age_category_ids)
        )
    ).scalars().all()

    session_url = (
        f"{settings.frontend_base_url}/sessions/{training_session.id}"
    )

    email_sender = ConsoleEmailSender()

    for user in users:
        email_sender.send(
            EmailMessage(
                to_email=user.email,
                subject=(
                    f"New training session available: "
                    f"{training_session.title}"
                ),
                body=(
                    f"Hello {user.first_name},\n\n"
                    "A new training session has been posted:\n\n"
                    f"Title: {training_session.title}\n"
                    f"Date: {training_session.date}\n"
                    f"Start time: {training_session.start_time}\n"
                    f"Duration: {training_session.duration_minutes} minutes\n"
                    f"Instructor: {training_session.instructor_name}\n\n"
                    f"Description:\n{training_session.description}\n\n"
                    "You can log in to the 7.77 Training Platform to "
                    "register for this session:\n"
                    f"{session_url}\n\n"
                    "The link to join the session will be available "
                    "one hour before it starts.\n\n"
                    "Thank you,\n"
                    "7.77 Training Platform"
                ),
            )
        )

def send_session_cancellation_emails(
    db: Session,
    training_session: TrainingSession,
) -> None:
    registered_users = db.execute(
        select(User)
        .join(
            Registration,
            Registration.user_id == User.id,
        )
        .where(
            Registration.session_id == training_session.id,
        )
    ).scalars().all()

    email_sender = ConsoleEmailSender()

    for user in registered_users:
        email_sender.send(
            EmailMessage(
                to_email=user.email,
                subject=f"Session cancelled: {training_session.title}",
                body=(
                    f"Hello {user.first_name},\n\n"
                    f"The training session "
                    f"\"{training_session.title}\" scheduled for "
                    f"{training_session.date} at "
                    f"{training_session.start_time} has been cancelled.\n\n"
                    "We apologize for any inconvenience."
                ),
            )
        )
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.registration import Registration
from app.models.session import Session as TrainingSession
from app.models.user import User
from app.notifications.email import ConsoleEmailSender, EmailMessage


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
from dataclasses import dataclass
from typing import Protocol

import logging


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailMessage:
    to_email: str
    subject: str
    body: str


class EmailSender(Protocol):
    def send(self, message: EmailMessage) -> None:
        ...


class ConsoleEmailSender:
    def send(self, message: EmailMessage) -> None:
        print(
            "EMAIL\n"
            f"To: {message.to_email}\n"
            f"Subject: {message.subject}\n"
            f"Body:\n{message.body}"
        )


def send_email_safely(
    email_sender: EmailSender,
    message: EmailMessage,
) -> None:
    try:
        email_sender.send(message)
    except Exception:
        logger.exception(
            "Failed to send email to %s",
            message.to_email,
        )
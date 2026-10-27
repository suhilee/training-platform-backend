from dataclasses import dataclass
from typing import Protocol


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

from app.notifications.email import (
    ConsoleEmailSender,
    EmailMessage,
    send_email_safely,
)


def test_console_email_sender_prints_message(capsys) -> None:
    sender = ConsoleEmailSender()

    message = EmailMessage(
        to_email="participant@example.com",
        subject="Password reset",
        body="Use this code to reset your password.",
    )

    sender.send(message)

    output = capsys.readouterr().out

    assert "participant@example.com" in output
    assert "Password reset" in output
    assert "Use this code to reset your password." in output

def test_send_email_safely_does_not_raise_when_sender_fails():
    class FailingEmailSender:
        def send(self, message):
            raise RuntimeError("SMTP server unavailable")

    message = EmailMessage(
        to_email="user@example.com",
        subject="Test",
        body="Test body",
    )

    send_email_safely(FailingEmailSender(), message)
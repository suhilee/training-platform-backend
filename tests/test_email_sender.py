from app.notifications.email import ConsoleEmailSender, EmailMessage


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

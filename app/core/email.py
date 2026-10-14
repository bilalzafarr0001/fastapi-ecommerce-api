"""
Fake email service.

A real project would talk to an SMTP server or a provider like SendGrid.
Here we only wait a bit and log the email, so you can SEE background tasks
running in the console AFTER the response was already sent to the client.
"""
import logging
import time

logger = logging.getLogger("app.email")

FAKE_DELAY_SECONDS = 2  # pretend we are talking to a slow email server


def send_email(to: str, subject: str, body: str) -> None:
    time.sleep(FAKE_DELAY_SECONDS)
    logger.info("Email sent to=%s subject=%r body=%r", to, subject, body)

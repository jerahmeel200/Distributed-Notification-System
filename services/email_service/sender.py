"""
Email Sender - Supports SendGrid and SMTP
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from typing import Optional
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.logger import get_logger
from shared.retry import retry_with_backoff

logger = get_logger(__name__)


class EmailSender:
    def __init__(self):
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM", "noreply@example.com")

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def send(self, to_email: str, subject: str, body: str) -> bool:
        """Send email using SendGrid or SMTP"""
        if self.sendgrid_api_key:
            return self._send_via_sendgrid(to_email, subject, body)
        elif self.smtp_user and self.smtp_password:
            return self._send_via_smtp(to_email, subject, body)
        else:
            logger.warning("No email configuration found, using mock sender")
            return self._send_mock(to_email, subject, body)

    def _send_via_sendgrid(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via SendGrid API"""
        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": self.email_from},
                "subject": subject,
                "content": [{"type": "text/html", "value": body}]
            }
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Email sent via SendGrid to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            raise

    def _send_via_smtp(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_from
            msg["To"] = to_email

            html_part = MIMEText(body, "html")
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent via SMTP to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise

    def _send_mock(self, to_email: str, subject: str, body: str) -> bool:
        """Mock email sender for development"""
        logger.info(f"[MOCK] Email to {to_email}: {subject}")
        logger.debug(f"[MOCK] Body: {body[:100]}...")
        return True


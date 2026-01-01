"""
Email Sender Service - Send HTML emails via SMTP (#301)

Simple SMTP email sender for automated reports.
Uses Bensley Axigen mail server by default.

Configuration via environment variables:
- SMTP_HOST: SMTP server (default: tmail.bensley.com)
- SMTP_PORT: SMTP port (default: 465 for SSL)
- SMTP_USER: Email account username
- SMTP_PASSWORD: Email account password
- REPORT_EMAIL_TO: Default recipient for reports
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


class EmailSender:
    """Send emails via SMTP."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize email sender with SMTP configuration.

        Args:
            host: SMTP server hostname (default from SMTP_HOST env)
            port: SMTP port (default from SMTP_PORT env, or 465)
            username: SMTP username (default from SMTP_USER env)
            password: SMTP password (default from SMTP_PASSWORD env)
        """
        self.host = host or os.getenv('SMTP_HOST', 'tmail.bensley.com')
        self.port = port or int(os.getenv('SMTP_PORT', '465'))
        self.username = username or os.getenv('SMTP_USER', '')
        self.password = password or os.getenv('SMTP_PASSWORD', '')

    def is_configured(self) -> bool:
        """Check if SMTP credentials are configured."""
        return bool(self.username and self.password)

    def send_html_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        from_name: str = "Bensley Reports",
        cc: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send an HTML email.

        Args:
            to: Recipient email address
            subject: Email subject line
            html_content: HTML body content
            from_name: Display name for sender
            cc: Optional list of CC recipients
            reply_to: Optional reply-to address

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.error("SMTP not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{self.username}>"
            msg['To'] = to

            if cc:
                msg['Cc'] = ', '.join(cc)

            if reply_to:
                msg['Reply-To'] = reply_to

            # Create plain text version (fallback)
            plain_text = f"This email requires an HTML-capable email client.\n\nView the report at: http://localhost:3002/overview"
            msg.attach(MIMEText(plain_text, 'plain'))

            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))

            # Build recipient list
            recipients = [to]
            if cc:
                recipients.extend(cc)

            # Create secure SSL context
            context = ssl.create_default_context()

            # Connect and send
            logger.info(f"Connecting to {self.host}:{self.port}...")

            with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
                logger.info(f"Logging in as {self.username}...")
                server.login(self.username, self.password)

                logger.info(f"Sending email to {to}...")
                server.sendmail(self.username, recipients, msg.as_string())

            logger.info(f"Email sent successfully to {to}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD. Error: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


def send_email(
    to: str,
    subject: str,
    html_content: str,
    from_name: str = "Bensley Reports",
    cc: Optional[List[str]] = None
) -> bool:
    """
    Convenience function to send an email.

    Args:
        to: Recipient email address
        subject: Email subject
        html_content: HTML body
        from_name: Sender display name
        cc: Optional CC list

    Returns:
        True if sent, False otherwise
    """
    sender = EmailSender()
    return sender.send_html_email(to, subject, html_content, from_name, cc)


def main():
    """CLI entry point for testing."""
    import sys

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Check configuration
    sender = EmailSender()

    if not sender.is_configured():
        print("ERROR: SMTP not configured.")
        print("Set these environment variables:")
        print("  SMTP_USER=your-email@gmail.com")
        print("  SMTP_PASSWORD=your-app-password")
        sys.exit(1)

    # Test email
    test_to = os.getenv('REPORT_EMAIL_TO', 'lukas@bensley.com')

    print(f"Sending test email to {test_to}...")

    html = f"""
    <html>
    <body style="font-family: sans-serif; padding: 20px;">
        <h1>Test Email from Bensley Reports</h1>
        <p>If you're reading this, email sending is working!</p>
        <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </body>
    </html>
    """

    success = sender.send_html_email(
        to=test_to,
        subject="Test - Bensley Report Email",
        html_content=html
    )

    if success:
        print(f"SUCCESS: Test email sent to {test_to}")
    else:
        print("FAILED: Could not send test email. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

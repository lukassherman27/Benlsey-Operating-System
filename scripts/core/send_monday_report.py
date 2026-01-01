#!/usr/bin/env python3
"""
Send Monday Morning Report - Weekly Proposal Email (#301)

Generates the weekly proposal report and emails it to Bill/Lukas.
Designed to run via launchd every Monday at 7am.

Usage:
    python scripts/core/send_monday_report.py              # Send report
    python scripts/core/send_monday_report.py --dry-run    # Generate only, don't send
    python scripts/core/send_monday_report.py --test       # Send test email

Environment variables:
    SMTP_USER: Gmail address for sending
    SMTP_PASSWORD: Gmail App Password
    REPORT_EMAIL_TO: Recipient email (default: lukas@bensley.com)
    DATABASE_PATH: Path to database (default: database/bensley_master.db)
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

# Load .env if present
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from backend.services.weekly_report_service import WeeklyReportService
from backend.services.email_sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/bensley-monday-report.log')
    ]
)
logger = logging.getLogger(__name__)


def get_report_subject() -> str:
    """Generate email subject with date."""
    today = datetime.now()
    week_num = today.isocalendar()[1]
    return f"Weekly Proposal Report - Week {week_num} ({today.strftime('%B %d, %Y')})"


def save_html_backup(html: str, reports_dir: Path) -> Path:
    """Save HTML report as backup file."""
    reports_dir.mkdir(exist_ok=True)
    filename = f"weekly-report-{datetime.now().strftime('%Y-%m-%d')}.html"
    filepath = reports_dir / filename
    filepath.write_text(html)
    return filepath


def archive_report(report_data: dict) -> None:
    """Archive report to database."""
    import sqlite3
    import json

    db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        period = report_data.get('period', {})
        week_review = report_data.get('week_in_review', {})
        pipeline = report_data.get('pipeline_outlook', {})
        attention = report_data.get('attention_required', {})

        cursor.execute("""
            INSERT INTO weekly_proposal_reports (
                report_date,
                week_ending,
                pdf_path,
                proposals_count,
                total_pipeline_value,
                win_rate,
                stale_count,
                new_this_week,
                won_this_week,
                lost_this_week,
                report_data,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            period.get('end', datetime.now().strftime('%Y-%m-%d')),
            period.get('end', datetime.now().strftime('%Y-%m-%d')),
            '',
            pipeline.get('proposal_count', 0),
            pipeline.get('total_pipeline', 0),
            pipeline.get('win_rate', {}).get('current', 0),
            attention.get('stale_count', 0),
            week_review.get('new_proposals', {}).get('count', 0),
            week_review.get('won', {}).get('count', 0),
            week_review.get('lost', {}).get('count', 0),
            json.dumps(report_data),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()
        logger.info("Report archived to database")

    except Exception as e:
        logger.warning(f"Failed to archive report: {e}")


def send_test_email(email_sender: EmailSender, to: str) -> bool:
    """Send a simple test email."""
    html = f"""
    <html>
    <body style="font-family: -apple-system, sans-serif; padding: 20px; background: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px;">
            <h1 style="color: #1e3a8a;">Test Email - Bensley Reports</h1>
            <p>If you're reading this, the Monday report email system is configured correctly!</p>
            <p style="color: #666;">Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">
                This is a test email. The real weekly report will include pipeline stats, attention items, and top opportunities.
            </p>
        </div>
    </body>
    </html>
    """

    return email_sender.send_html_email(
        to=to,
        subject="Test - Bensley Weekly Report System",
        html_content=html
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Send weekly proposal report email')
    parser.add_argument('--dry-run', action='store_true',
                        help='Generate report but do not send email')
    parser.add_argument('--test', action='store_true',
                        help='Send a test email instead of the full report')
    parser.add_argument('--to', type=str,
                        help='Override recipient email address')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Monday Morning Report - Starting")
    logger.info("=" * 60)

    # Get recipient
    recipient = args.to or os.getenv('REPORT_EMAIL_TO', 'lukas@bensley.com')
    logger.info(f"Recipient: {recipient}")

    # Initialize email sender
    email_sender = EmailSender()

    # Check SMTP config (skip for dry-run)
    if not args.dry_run and not email_sender.is_configured():
        logger.error("SMTP not configured!")
        logger.error("Set SMTP_USER and SMTP_PASSWORD in .env")
        sys.exit(1)

    # Test mode
    if args.test:
        logger.info("Sending test email...")
        success = send_test_email(email_sender, recipient)
        if success:
            logger.info("Test email sent successfully!")
            sys.exit(0)
        else:
            logger.error("Failed to send test email")
            sys.exit(1)

    # Generate report
    logger.info("Generating weekly report...")

    db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
    report_service = WeeklyReportService(db_path)

    # Get both JSON data and HTML
    report_data = report_service.generate_report()
    html_content = report_service.generate_html_report()

    # Log key metrics
    pipeline = report_data.get('pipeline_outlook', {})
    logger.info(f"Pipeline: ${pipeline.get('total_pipeline', 0):,.0f}")
    logger.info(f"Proposals: {pipeline.get('proposal_count', 0)}")
    logger.info(f"Win Rate: {pipeline.get('win_rate', {}).get('current', 0):.1f}%")

    # Save backup
    reports_dir = PROJECT_ROOT / 'reports'
    backup_path = save_html_backup(html_content, reports_dir)
    logger.info(f"HTML backup saved: {backup_path}")

    # Archive to database
    archive_report(report_data)

    # Dry run - don't send
    if args.dry_run:
        logger.info("DRY RUN - Email not sent")
        logger.info(f"View report at: {backup_path}")
        sys.exit(0)

    # Send email
    logger.info(f"Sending email to {recipient}...")
    subject = get_report_subject()

    success = email_sender.send_html_email(
        to=recipient,
        subject=subject,
        html_content=html_content
    )

    if success:
        logger.info("=" * 60)
        logger.info("SUCCESS - Weekly report sent!")
        logger.info(f"Recipient: {recipient}")
        logger.info(f"Subject: {subject}")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("FAILED - Could not send email")
        logger.error(f"HTML backup available at: {backup_path}")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

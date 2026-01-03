#!/usr/bin/env python3
"""
Schedule Emailer - Automated weekly schedule delivery to Bill
Sends clean PDFs every Friday evening
"""

import sqlite3
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

DB_PATH = os.getenv('BENSLEY_DB_PATH', 'database/bensley_master.db')


class ScheduleEmailer:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None

        # Email configuration
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', 'lukas@bensley.com')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.bill_email = 'bill@bensley.com'

    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_current_week_schedules(self) -> List[Dict]:
        """Get schedules for the current week"""
        cursor = self.conn.cursor()

        # Get current week Monday
        today = datetime.now()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        week_start_str = week_start.strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT schedule_id, office, week_start_date, week_end_date, pdf_path
            FROM weekly_schedules
            WHERE week_start_date = ?
            ORDER BY office
        """, (week_start_str,))

        return [dict(row) for row in cursor.fetchall()]

    def generate_missing_pdfs(self, schedules: List[Dict]) -> List[Dict]:
        """Generate PDFs for schedules that don't have them yet"""
        from schedule_pdf_generator import SchedulePDFGenerator

        generator = SchedulePDFGenerator(self.db_path)
        generator.connect()

        updated_schedules = []
        for schedule in schedules:
            schedule_id = schedule['schedule_id']
            office = schedule['office']
            pdf_path = schedule['pdf_path']

            # Check if PDF exists
            if not pdf_path or not Path(pdf_path).exists():
                # Generate new PDF - use persistent directory, not /tmp
                output_dir = os.getenv('SCHEDULE_OUTPUT_DIR', os.path.join(os.path.dirname(self.db_path), 'schedules'))
                os.makedirs(output_dir, exist_ok=True)
                filename = f"Bensley_Schedule_{office}_{schedule['week_start_date']}.pdf"
                output_path = os.path.join(output_dir, filename)

                success = generator.generate_schedule_pdf(schedule_id, output_path)
                if success:
                    schedule['pdf_path'] = output_path
                    print(f"Generated PDF for {office}: {output_path}")

            updated_schedules.append(schedule)

        generator.close()
        return updated_schedules

    def send_weekly_schedules(self, recipient: Optional[str] = None, test_mode: bool = False):
        """
        Send weekly schedule PDFs to Bill

        Args:
            recipient: Override recipient email (for testing)
            test_mode: If True, print email instead of sending
        """
        schedules = self.get_current_week_schedules()

        if not schedules:
            print("No schedules found for current week")
            return False

        # Generate missing PDFs
        schedules = self.generate_missing_pdfs(schedules)

        # Group by office
        bali_schedule = next((s for s in schedules if s['office'] == 'Bali'), None)
        bangkok_schedule = next((s for s in schedules if s['office'] == 'Bangkok'), None)

        if not bali_schedule and not bangkok_schedule:
            print("No schedules with PDFs available")
            return False

        # Prepare email
        week_start = schedules[0]['week_start_date']
        week_end = schedules[0]['week_end_date']
        week_start_dt = datetime.strptime(week_start, "%Y-%m-%d")
        week_end_dt = datetime.strptime(week_end, "%Y-%m-%d")

        subject = f"Weekly Schedule - {week_start_dt.strftime('%b %d')} - {week_end_dt.strftime('%b %d, %Y')}"

        # Email body
        body = f"""Hi Bill,

Here are the team schedules for the week of {week_start_dt.strftime('%B %d')} - {week_end_dt.strftime('%B %d, %Y')}:

"""

        if bali_schedule:
            body += f"- Bali Office: {Path(bali_schedule['pdf_path']).name}\n"
        if bangkok_schedule:
            body += f"- Bangkok Office: {Path(bangkok_schedule['pdf_path']).name}\n"

        body += """
Best regards,
Bensley Scheduling System
"""

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = recipient or self.bill_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Attach PDFs
        attachments = []
        if bali_schedule and bali_schedule['pdf_path']:
            attachments.append(bali_schedule['pdf_path'])
        if bangkok_schedule and bangkok_schedule['pdf_path']:
            attachments.append(bangkok_schedule['pdf_path'])

        for pdf_path in attachments:
            if Path(pdf_path).exists():
                with open(pdf_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    pdf_attachment.add_header('Content-Disposition', 'attachment',
                                            filename=Path(pdf_path).name)
                    msg.attach(pdf_attachment)
                print(f"Attached: {Path(pdf_path).name}")

        # Send or print
        if test_mode:
            print("\n" + "="*60)
            print("TEST MODE - Email would be sent:")
            print("="*60)
            print(f"From: {msg['From']}")
            print(f"To: {msg['To']}")
            print(f"Subject: {msg['Subject']}")
            print(f"\n{body}")
            print(f"Attachments: {len(attachments)}")
            for att in attachments:
                print(f"  - {Path(att).name}")
            print("="*60)
            return True
        else:
            try:
                # Send email
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

                print(f"✅ Email sent to {msg['To']}")

                # Log the send
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO schedule_email_log (schedule_ids, recipient, subject, sent_at)
                    VALUES (?, ?, ?, datetime('now'))
                """, (
                    ','.join(str(s['schedule_id']) for s in schedules),
                    msg['To'],
                    subject
                ))
                self.conn.commit()

                return True
            except Exception as e:
                print(f"❌ Failed to send email: {e}")
                return False

    def send_monthly_summary(self, year: int, month: int, recipient: Optional[str] = None, test_mode: bool = False):
        """
        Send monthly consolidated schedule summary

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            recipient: Override recipient email
            test_mode: If True, print instead of sending
        """
        cursor = self.conn.cursor()

        # Get all schedules for the month
        month_start = f"{year}-{month:02d}-01"
        if month == 12:
            month_end = f"{year+1}-01-01"
        else:
            month_end = f"{year}-{month+1:02d}-01"

        cursor.execute("""
            SELECT schedule_id, office, week_start_date, week_end_date
            FROM weekly_schedules
            WHERE week_start_date >= ? AND week_start_date < ?
            ORDER BY office, week_start_date
        """, (month_start, month_end))

        schedules = [dict(row) for row in cursor.fetchall()]

        if not schedules:
            print(f"No schedules found for {year}-{month:02d}")
            return False

        month_name = datetime(year, month, 1).strftime("%B %Y")
        subject = f"Monthly Schedule Summary - {month_name}"

        # Build summary body
        body = f"""Hi Bill,

Here's the schedule summary for {month_name}:

"""

        # Group by office
        for office in ['Bali', 'Bangkok']:
            office_schedules = [s for s in schedules if s['office'] == office]
            if office_schedules:
                body += f"\n{office} Office:\n"
                for sched in office_schedules:
                    week_start = datetime.strptime(sched['week_start_date'], "%Y-%m-%d")
                    week_end = datetime.strptime(sched['week_end_date'], "%Y-%m-%d")
                    body += f"  - Week of {week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}\n"

        body += """
Best regards,
Bensley Scheduling System
"""

        # Create email
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = recipient or self.bill_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if test_mode:
            print("\n" + "="*60)
            print("TEST MODE - Monthly summary would be sent:")
            print("="*60)
            print(f"From: {msg['From']}")
            print(f"To: {msg['To']}")
            print(f"Subject: {msg['Subject']}")
            print(f"\n{body}")
            print("="*60)
            return True
        else:
            try:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

                print(f"✅ Monthly summary sent to {msg['To']}")
                return True
            except Exception as e:
                print(f"❌ Failed to send monthly summary: {e}")
                return False


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Send weekly schedule emails')
    parser.add_argument('--weekly', action='store_true', help='Send weekly schedules')
    parser.add_argument('--monthly', action='store_true', help='Send monthly summary')
    parser.add_argument('--month', type=int, help='Month for monthly summary (1-12)')
    parser.add_argument('--year', type=int, help='Year for monthly summary')
    parser.add_argument('--recipient', type=str, help='Override recipient email')
    parser.add_argument('--test', action='store_true', help='Test mode - print instead of sending')

    args = parser.parse_args()

    emailer = ScheduleEmailer()
    emailer.connect()

    try:
        if args.weekly:
            emailer.send_weekly_schedules(recipient=args.recipient, test_mode=args.test)
        elif args.monthly:
            year = args.year or datetime.now().year
            month = args.month or datetime.now().month
            emailer.send_monthly_summary(year, month, recipient=args.recipient, test_mode=args.test)
        else:
            print("Please specify --weekly or --monthly")
            parser.print_help()
    finally:
        emailer.close()


if __name__ == "__main__":
    main()

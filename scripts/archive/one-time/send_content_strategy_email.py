#!/usr/bin/env python3
"""
Send Content Strategy Email to Lukas
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# Read the markdown file
content_file = Path(__file__).parent.parent / "files" / "BENSLEY_CONTENT_STRATEGY_2025.md"

with open(content_file, 'r') as f:
    content = f.read()

# Email configuration - using tmail SMTP
smtp_host = "tmail.bensley.com"
smtp_port = 587  # or 465 for SSL
smtp_user = "lukas@bensley.com"
smtp_password = "0823356345"

# Create email
msg = MIMEMultipart('alternative')
msg['From'] = smtp_user
msg['To'] = smtp_user  # sending to yourself
msg['Subject'] = "BENSLEY CONTENT STRATEGY 2025 - Full Plan"

# Plain text version
msg.attach(MIMEText(content, 'plain'))

# Try to send
print(f"Attempting to send email via {smtp_host}:{smtp_port}...")

try:
    # Try TLS first (port 587)
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.set_debuglevel(1)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"TLS attempt failed: {e}")
    print("\nTrying SSL on port 465...")
    try:
        with smtplib.SMTP_SSL(smtp_host, 465, timeout=30) as server:
            server.set_debuglevel(1)
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print("✅ Email sent successfully via SSL!")
    except Exception as e2:
        print(f"SSL attempt also failed: {e2}")
        print("\n❌ Could not send email. Please check SMTP settings.")
        print("\nThe content is saved at:")
        print(f"  {content_file}")
        print("\nYou can copy it manually from there.")

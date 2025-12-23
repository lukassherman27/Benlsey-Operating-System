#!/usr/bin/env python3
"""
Send La Vie Follow-up Email Draft to Lukas with Tax Attachments
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Email configuration
smtp_host = "tmail.bensley.com"
smtp_port = 587
smtp_user = "lukas@bensley.com"
smtp_password = "0823356345"

# Attachments - India tax documents from TARC emails
attachments = [
    "/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/2025-12/Certificate of Residence-India (Tax year 2025).pdf",
    "/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/2025-12/Bensley - Filed Form 10F (FY 2025-26) Ack.pdf",
    "/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/2025-12/Bensley - Filed Form 10F (FY 2025-26).pdf",
    "/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/2025-12/Declaration TRC 2025 (signed).pdf",
]

# Email content
subject = "DRAFT: La Vie Follow-up - Re: Thursday, 30th - Next Step Meeting"

body = """Hi all,

Hope this finds you well. Just following up - I understand you've been busy with permitting and government approvals, and hope everything is progressing smoothly on that front.

Please let us know if there's anything you need from our end to move this forward. I've attached the tax documentation regarding the Double Taxation Avoidance Agreement (DTAA) between India and Thailand for your reference:

- Certificate of Residence (India) - Tax year 2025
- Filed Form 10F (FY 2025-26) with Acknowledgment
- Declaration TRC 2025 (signed)

Our office will be on holiday from December 12th to January 5th, however we will be available to discuss and finalize contract terms during this period. That way, by the time we're back we can get some pens onto paper for this project.

Looking forward to hearing from you.

Best regards,

Lukas

---
TO: Nigel Franklyn <nigel@mosswellnessconsultancy.com>, Talluri Naga Satyakanth <nagasatyakanth.t@meghaeng.com>, Harsha Rupanagudi <harsha.r@meghaeng.com>
SUBJECT: Re: Thursday, 30th - Next Step Meeting
---
"""

# Create email
msg = MIMEMultipart()
msg['From'] = smtp_user
msg['To'] = smtp_user
msg['Subject'] = subject

msg.attach(MIMEText(body, 'plain'))

# Add attachments
for filepath in attachments:
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(filepath)}"')
            msg.attach(part)
        print(f"✓ Attached: {os.path.basename(filepath)}")
    else:
        print(f"✗ NOT FOUND: {filepath}")

# Send
print(f"\nSending email to {smtp_user}...")

try:
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    print("\n✅ Email sent successfully with attachments!")
except Exception as e:
    print(f"TLS failed: {e}")
    try:
        with smtplib.SMTP_SSL(smtp_host, 465, timeout=30) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print("\n✅ Email sent via SSL with attachments!")
    except Exception as e2:
        print(f"SSL also failed: {e2}")
        print("\n❌ Could not send. Copy the content above manually.")

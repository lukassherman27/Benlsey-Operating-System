#!/usr/bin/env python3
"""
Send the Instagram Strategy email to Bill
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email configuration - using SMTP (port 587 for TLS)
SMTP_HOST = os.getenv('EMAIL_SERVER', 'tmail.bensley.com')
SMTP_PORT = 587  # TLS port for sending
EMAIL_USER = os.getenv('EMAIL_USERNAME', 'lukas@bensley.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')

def read_email_content():
    """Read the markdown email draft"""
    email_path = Path(__file__).parent.parent / "docs/tasks/instagram-strategy-email-draft.md"
    with open(email_path, 'r') as f:
        content = f.read()

    # Skip the header metadata
    lines = content.split('\n')
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('Hi Bill,'):
            body_start = i
            break

    return '\n'.join(lines[body_start:])

def markdown_to_html(md_text):
    """Convert markdown to simple HTML for email"""
    html = md_text

    # Headers
    import re
    html = re.sub(r'^### (.+)$', r'<h3 style="color: #333; margin-top: 20px;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2 style="color: #222; margin-top: 25px; border-bottom: 1px solid #ddd; padding-bottom: 5px;">\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1 style="color: #111; margin-top: 30px;">\1</h1>', html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Blockquotes
    html = re.sub(r'^> (.+)$', r'<blockquote style="border-left: 3px solid #ccc; padding-left: 15px; margin: 15px 0; color: #555; font-style: italic;">\1</blockquote>', html, flags=re.MULTILINE)

    # Code blocks (preserve formatting)
    html = re.sub(r'```(.*?)```', r'<pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: monospace; font-size: 12px; line-height: 1.4;">\1</pre>', html, flags=re.DOTALL)

    # Tables - convert to HTML tables
    def convert_table(match):
        lines = match.group(0).strip().split('\n')
        if len(lines) < 2:
            return match.group(0)

        html_table = '<table style="border-collapse: collapse; width: 100%; margin: 15px 0;">'

        # Header row
        headers = [cell.strip() for cell in lines[0].split('|') if cell.strip()]
        html_table += '<tr>'
        for h in headers:
            html_table += f'<th style="border: 1px solid #ddd; padding: 10px; background: #f5f5f5; text-align: left;">{h}</th>'
        html_table += '</tr>'

        # Data rows (skip separator line)
        for line in lines[2:]:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                html_table += '<tr>'
                for cell in cells:
                    html_table += f'<td style="border: 1px solid #ddd; padding: 10px;">{cell}</td>'
                html_table += '</tr>'

        html_table += '</table>'
        return html_table

    # Find and convert tables
    table_pattern = r'(\|.+\|[\r\n]+\|[-: |]+\|[\r\n]+(?:\|.+\|[\r\n]*)+)'
    html = re.sub(table_pattern, convert_table, html)

    # Bullet points
    html = re.sub(r'^- (.+)$', r'<li style="margin: 5px 0;">\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li.*</li>\n)+', r'<ul style="margin: 10px 0; padding-left: 25px;">\g<0></ul>', html)

    # Numbered lists
    html = re.sub(r'^(\d+)\. (.+)$', r'<li style="margin: 5px 0;">\2</li>', html, flags=re.MULTILINE)

    # Horizontal rules
    html = re.sub(r'^---+$', r'<hr style="border: none; border-top: 1px solid #ddd; margin: 25px 0;">', html, flags=re.MULTILINE)

    # Paragraphs (double newlines)
    html = re.sub(r'\n\n', r'</p><p style="margin: 15px 0; line-height: 1.6;">', html)

    # Wrap in basic HTML structure
    html = f'''
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; line-height: 1.6;">
    <p style="margin: 15px 0; line-height: 1.6;">
    {html}
    </p>
    </body>
    </html>
    '''

    return html

def send_email(to_email: str, subject: str, body_text: str, body_html: str):
    """Send email via SMTP"""
    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach both plain text and HTML versions
    part1 = MIMEText(body_text, 'plain')
    part2 = MIMEText(body_html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    try:
        print(f"Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            print(f"Logging in as {EMAIL_USER}...")
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            print(f"Sending to {to_email}...")
            server.send_message(msg)
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        # Try alternate port
        try:
            print(f"Trying alternate port 465 (SSL)...")
            import ssl
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, 465, context=context) as server:
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.send_message(msg)
            print(f"✅ Email sent successfully to {to_email}")
            return True
        except Exception as e2:
            print(f"❌ Also failed with SSL: {e2}")
            return False

def main():
    # Read the email content
    body_text = read_email_content()
    body_html = markdown_to_html(body_text)

    # Send to lukas@bensley.com for review
    recipient = "lukas@bensley.com"
    subject = "Social Media Strategy + Bensley Brain Progress"

    print(f"\n{'='*60}")
    print(f"Sending strategy email to: {recipient}")
    print(f"Subject: {subject}")
    print(f"{'='*60}\n")

    send_email(recipient, subject, body_text, body_html)

if __name__ == "__main__":
    main()

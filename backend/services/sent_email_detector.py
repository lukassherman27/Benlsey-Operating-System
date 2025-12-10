#!/usr/bin/env python3
"""
Sent Email Detector - Scan Sent folder for proposal-related emails

This service:
1. Connects to IMAP Sent folder
2. Detects "proposal sent" patterns (attachments, subject keywords)
3. Creates suggestions for status updates (never auto-updates)
4. Links email as evidence for the status change

Usage:
    from backend.services.sent_email_detector import SentEmailDetector

    detector = SentEmailDetector()
    if detector.connect():
        results = detector.scan_sent_for_proposals(days_back=7)
        detector.close()
"""

import imaplib
import email
import re
import json
import sqlite3
import os
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root))
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


# Keywords that suggest a proposal email
PROPOSAL_SUBJECT_KEYWORDS = [
    'proposal',
    'quotation',
    'quote',
    'fee proposal',
    'design fee',
    'fee submittal',
    'scope of services',
    'professional services',
    'cost estimate',
    'budget proposal',
    'pricing',
]

# Attachment patterns that suggest proposal documents
PROPOSAL_ATTACHMENT_PATTERNS = [
    r'proposal.*\.pdf$',
    r'fee.*proposal.*\.pdf$',
    r'quotation.*\.pdf$',
    r'quote.*\.pdf$',
    r'.*scope.*services.*\.pdf$',
    r'.*\d{2}\s*BK[-\s]?\d{3}.*\.pdf$',  # Project code in filename
]

# Project code pattern (e.g., "24 BK-089", "25BK-015")
PROJECT_CODE_PATTERN = r'\b(\d{2}\s*BK[-\s]?\d{3})\b'


class SentEmailDetector:
    """
    Detects proposal-related emails in the Sent folder and creates
    suggestions for status updates.
    """

    def __init__(self, db_path: str = None):
        self.server = os.getenv('EMAIL_SERVER')
        self.port = int(os.getenv('EMAIL_PORT', 993))
        self.username = os.getenv('EMAIL_USER')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'database/bensley_master.db')
        self.imap = None

    def connect(self) -> bool:
        """Connect to IMAP server"""
        logger.info(f"Connecting to IMAP server: {self.server}:{self.port}")
        try:
            self.imap = imaplib.IMAP4_SSL(self.server, self.port)
            self.imap.login(self.username, self.password)
            logger.info("Successfully connected to IMAP server")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}", exc_info=True)
            return False

    def close(self):
        """Close IMAP connection"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except Exception:
                pass  # Connection may already be closed

    def get_sent_folder_name(self) -> Optional[str]:
        """
        Find the Sent folder name (varies by email server).
        Common names: 'Sent', 'SENT', 'Sent Items', 'Sent Messages'
        """
        try:
            status, folders = self.imap.list()
            for folder in folders:
                folder_str = folder.decode()
                # Check for common Sent folder names
                if any(name in folder_str.lower() for name in ['sent', 'sent items', 'sent messages']):
                    # Extract folder name from IMAP list response
                    # Format: (\\HasNoChildren \\Sent) "/" "Sent"
                    match = re.search(r'"([^"]*sent[^"]*)"', folder_str, re.IGNORECASE)
                    if match:
                        return match.group(1)
                    # Try without quotes
                    parts = folder_str.split()
                    if parts:
                        return parts[-1].strip('"')
            return 'Sent'  # Default fallback
        except Exception as e:
            logger.warning(f"Error finding Sent folder: {e}")
            return 'Sent'

    def scan_sent_for_proposals(
        self,
        days_back: int = 30,
        limit: int = 500
    ) -> Dict:
        """
        Scan Sent folder for proposal-related emails.

        Args:
            days_back: How many days back to scan
            limit: Maximum emails to process

        Returns:
            Dict with scan results and suggestions created
        """
        results = {
            'emails_scanned': 0,
            'proposals_detected': 0,
            'suggestions_created': 0,
            'errors': [],
            'detections': []
        }

        # Find Sent folder
        sent_folder = self.get_sent_folder_name()
        logger.info(f"Scanning Sent folder: {sent_folder}")

        try:
            status, _ = self.imap.select(sent_folder)
            if status != 'OK':
                results['errors'].append(f"Could not select folder: {sent_folder}")
                return results
        except Exception as e:
            results['errors'].append(f"Error selecting folder: {e}")
            return results

        # Search for emails in date range
        since_date = (datetime.now() - timedelta(days=days_back)).strftime('%d-%b-%Y')
        try:
            status, messages = self.imap.search(None, f'(SINCE {since_date})')
            email_ids = messages[0].split()
        except Exception as e:
            results['errors'].append(f"Error searching emails: {e}")
            return results

        # Limit to most recent
        email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        logger.info(f"Found {len(email_ids)} sent emails to scan")

        # Get existing proposals for matching
        proposals = self._get_active_proposals()

        # Get already-processed sent emails to avoid duplicates
        processed_message_ids = self._get_processed_sent_emails()

        for email_id in email_ids:
            try:
                detection = self._process_sent_email(email_id, proposals, processed_message_ids)
                results['emails_scanned'] += 1

                if detection:
                    results['proposals_detected'] += 1
                    results['detections'].append(detection)

                    # Create suggestion (if not already exists)
                    suggestion_created = self._create_status_suggestion(detection)
                    if suggestion_created:
                        results['suggestions_created'] += 1

            except Exception as e:
                logger.warning(f"Error processing email {email_id}: {e}")
                results['errors'].append(str(e))

        logger.info(
            f"Scan complete: {results['emails_scanned']} scanned, "
            f"{results['proposals_detected']} proposals detected, "
            f"{results['suggestions_created']} suggestions created"
        )
        return results

    def _process_sent_email(
        self,
        email_id: bytes,
        proposals: List[Dict],
        processed_message_ids: set
    ) -> Optional[Dict]:
        """
        Process a single sent email to detect proposal patterns.

        Returns detection info if this appears to be a proposal email.
        """
        # Fetch email
        status, msg_data = self.imap.fetch(email_id, '(RFC822)')

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                # Get message ID
                message_id = msg.get('Message-ID', f"sent-{email_id.decode()}")

                # Skip if already processed
                if message_id in processed_message_ids:
                    return None

                # Extract fields
                subject = self._decode_header(msg.get('Subject', ''))
                recipients = msg.get('To', '')
                date_str = msg.get('Date', '')

                # Parse date
                try:
                    email_date = parsedate_to_datetime(date_str)
                except (ValueError, TypeError):
                    email_date = datetime.now()

                # Get body text
                body = self._get_email_body(msg)

                # Get attachments info
                attachments = self._get_attachment_info(msg)

                # Detect if this is a proposal email
                is_proposal, confidence, detection_reasons = self._detect_proposal_email(
                    subject, body, attachments
                )

                if not is_proposal:
                    return None

                # Try to match to a specific proposal
                matched_proposal = self._match_to_proposal(
                    subject, body, attachments, recipients, proposals
                )

                if not matched_proposal:
                    return None  # Only create suggestions for matched proposals

                return {
                    'message_id': message_id,
                    'subject': subject,
                    'recipients': recipients,
                    'email_date': email_date.isoformat(),
                    'date_normalized': email_date.strftime('%Y-%m-%d'),
                    'confidence': confidence,
                    'detection_reasons': detection_reasons,
                    'attachments': attachments,
                    'matched_proposal': matched_proposal
                }

        return None

    def _detect_proposal_email(
        self,
        subject: str,
        body: str,
        attachments: List[Dict]
    ) -> Tuple[bool, float, List[str]]:
        """
        Detect if this email appears to be sending a proposal.

        Returns:
            Tuple of (is_proposal, confidence_score, detection_reasons)
        """
        reasons = []
        confidence = 0.0

        subject_lower = subject.lower()
        body_lower = body.lower()
        text = f"{subject_lower} {body_lower}"

        # Check subject keywords
        for keyword in PROPOSAL_SUBJECT_KEYWORDS:
            if keyword in subject_lower:
                reasons.append(f"Subject contains '{keyword}'")
                confidence += 0.3
                break

        # Check for proposal-related attachments
        proposal_attachments = []
        for att in attachments:
            filename_lower = att['filename'].lower()
            for pattern in PROPOSAL_ATTACHMENT_PATTERNS:
                if re.match(pattern, filename_lower):
                    proposal_attachments.append(att['filename'])
                    confidence += 0.4
                    break

        if proposal_attachments:
            reasons.append(f"Proposal attachments: {', '.join(proposal_attachments[:3])}")

        # Check for PDF attachments with significant size (> 100KB likely a document)
        pdf_attachments = [a for a in attachments if a['filename'].lower().endswith('.pdf')]
        if pdf_attachments:
            large_pdfs = [a for a in pdf_attachments if a.get('size', 0) > 100000]
            if large_pdfs:
                reasons.append(f"{len(large_pdfs)} substantial PDF attachment(s)")
                confidence += 0.2

        # Check body for proposal-related phrases
        proposal_phrases = [
            'please find attached',
            'enclosed please find',
            'attached is our proposal',
            'attached proposal',
            'fee proposal',
            'scope of services',
            'design services',
            'professional fees'
        ]
        for phrase in proposal_phrases:
            if phrase in text:
                reasons.append(f"Body contains '{phrase}'")
                confidence += 0.2
                break

        # Cap confidence at 0.95
        confidence = min(0.95, confidence)

        # Minimum threshold
        is_proposal = confidence >= 0.4 and len(reasons) >= 1

        return is_proposal, confidence, reasons

    def _match_to_proposal(
        self,
        subject: str,
        body: str,
        attachments: List[Dict],
        recipients: str,
        proposals: List[Dict]
    ) -> Optional[Dict]:
        """
        Try to match this email to a specific proposal in the database.

        Returns matched proposal info or None.
        """
        text = f"{subject} {body}"

        # Priority 1: Check for project code in subject, body, or attachments
        code_matches = re.findall(PROJECT_CODE_PATTERN, text, re.IGNORECASE)
        for att in attachments:
            code_matches.extend(re.findall(PROJECT_CODE_PATTERN, att['filename'], re.IGNORECASE))

        for match in code_matches:
            # Normalize project code
            normalized = self._normalize_project_code(match)
            for proposal in proposals:
                if proposal['project_code'] == normalized:
                    return {
                        'proposal_id': proposal['proposal_id'],
                        'project_code': proposal['project_code'],
                        'project_name': proposal['project_name'],
                        'current_status': proposal['status'],
                        'match_type': 'project_code',
                        'match_confidence': 0.95
                    }

        # Priority 2: Match by project/client name
        text_lower = text.lower()
        recipients_lower = recipients.lower()

        best_match = None
        best_score = 0

        for proposal in proposals:
            score = 0
            match_reasons = []

            # Check project name
            proj_name = (proposal.get('project_name') or '').lower()
            if proj_name and len(proj_name) > 4 and proj_name in text_lower:
                score += 0.6
                match_reasons.append('project_name_in_text')

            # Check client company
            client = (proposal.get('client_company') or '').lower()
            if client and len(client) > 3 and client in text_lower:
                score += 0.5
                match_reasons.append('client_in_text')

            # Check contact email
            contact_email = (proposal.get('contact_email') or '').lower()
            if contact_email and contact_email in recipients_lower:
                score += 0.4
                match_reasons.append('contact_email_match')

            if score > best_score and score >= 0.5:
                best_score = score
                best_match = {
                    'proposal_id': proposal['proposal_id'],
                    'project_code': proposal['project_code'],
                    'project_name': proposal['project_name'],
                    'current_status': proposal['status'],
                    'match_type': '+'.join(match_reasons),
                    'match_confidence': min(0.85, score)
                }

        return best_match

    def _normalize_project_code(self, code: str) -> str:
        """Normalize project code to standard format: 'XX BK-XXX'"""
        # Remove extra spaces, normalize dashes
        normalized = re.sub(r'[\s-]+', ' ', code.upper()).strip()
        # Convert to standard format
        normalized = re.sub(r'(\d{2})\s*BK\s*(\d{3})', r'\1 BK-\2', normalized)
        return normalized

    def _create_status_suggestion(self, detection: Dict) -> bool:
        """
        Create a proposal_status_update suggestion in the database.

        Returns True if suggestion was created, False if skipped (duplicate).
        """
        matched = detection['matched_proposal']
        project_code = matched['project_code']
        current_status = matched['current_status']

        # Skip if already in proposal_sent or later status
        later_statuses = ['proposal_sent', 'awaiting_response', 'negotiation', 'won', 'lost']
        if current_status in later_statuses:
            logger.debug(f"Skipping {project_code}: already in status '{current_status}'")
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check for existing pending suggestion for this proposal
            cursor.execute("""
                SELECT suggestion_id FROM ai_suggestions
                WHERE suggestion_type = 'proposal_status_update'
                AND project_code = ?
                AND status = 'pending'
                AND json_extract(suggested_data, '$.new_status') = 'proposal_sent'
            """, (project_code,))

            if cursor.fetchone():
                logger.debug(f"Skipping {project_code}: pending suggestion already exists")
                conn.close()
                return False

            # Store the sent email in database first if not exists
            email_id = self._ensure_email_in_database(detection, conn)

            # Create the suggestion
            suggested_data = json.dumps({
                'new_status': 'proposal_sent',
                'project_code': project_code,
                'proposal_id': matched['proposal_id'],
                'email_date': detection['date_normalized'],
                'evidence_email_id': email_id,
                'match_type': matched['match_type'],
                'detection_reasons': detection['detection_reasons'],
                'attachments': [a['filename'] for a in detection['attachments'][:5]]
            })

            cursor.execute("""
                INSERT INTO ai_suggestions (
                    suggestion_type, priority, confidence_score,
                    source_type, source_id, source_reference,
                    title, description, suggested_action,
                    suggested_data, target_table, project_code,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
            """, (
                'proposal_status_update',
                'high',
                detection['confidence'] * matched['match_confidence'],
                'sent_email',
                email_id,
                f"Sent email: {detection['subject'][:50]}",
                f"Update {project_code} status to 'proposal_sent'",
                f"Detected proposal email sent on {detection['date_normalized']}. "
                f"Reasons: {', '.join(detection['detection_reasons'])}. "
                f"Matched via: {matched['match_type']}",
                "Update proposal status to 'proposal_sent' and record sent date",
                suggested_data,
                'proposals',
                project_code
            ))

            conn.commit()
            logger.info(f"Created status suggestion for {project_code}")
            return True

        except Exception as e:
            logger.error(f"Error creating suggestion: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()

    def _ensure_email_in_database(self, detection: Dict, conn: sqlite3.Connection) -> Optional[int]:
        """
        Ensure the sent email is stored in the emails table.

        Returns the email_id.
        """
        cursor = conn.cursor()

        # Check if already exists
        cursor.execute(
            "SELECT email_id FROM emails WHERE message_id = ?",
            (detection['message_id'],)
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        # Insert the email
        cursor.execute("""
            INSERT INTO emails
            (message_id, sender_email, recipient_emails, subject, snippet, date, date_normalized, processed, has_attachments, folder)
            VALUES (?, ?, ?, ?, ?, ?, datetime(?), 1, ?, 'Sent')
        """, (
            detection['message_id'],
            self.username,  # Sender is us
            detection['recipients'],
            detection['subject'],
            detection['subject'][:200],  # Use subject as snippet
            detection['email_date'],
            detection['email_date'],
            1 if detection['attachments'] else 0
        ))
        conn.commit()

        return cursor.lastrowid

    def _get_active_proposals(self) -> List[Dict]:
        """Get proposals that could receive proposal_sent status."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT proposal_id, project_code, project_name, client_company,
                   contact_email, status
            FROM proposals
            WHERE status NOT IN ('won', 'lost', 'cancelled')
            ORDER BY created_at DESC
        """)

        proposals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return proposals

    def _get_processed_sent_emails(self) -> set:
        """Get message IDs of sent emails already processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT message_id FROM emails WHERE folder = 'Sent'
        """)

        message_ids = {row[0] for row in cursor.fetchall()}
        conn.close()
        return message_ids

    def _decode_header(self, header: str) -> str:
        """Decode email header value."""
        if not header:
            return ""
        decoded = decode_header(header)
        parts = []
        for part, encoding in decoded:
            if isinstance(part, bytes):
                parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                parts.append(part)
        return ''.join(parts)

    def _get_email_body(self, msg) -> str:
        """Extract plain text body from email."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except (AttributeError, UnicodeDecodeError):
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except (AttributeError, UnicodeDecodeError):
                pass
        return body[:5000]  # Limit for processing

    def _get_attachment_info(self, msg) -> List[Dict]:
        """Get info about email attachments without downloading them."""
        attachments = []

        if not msg.is_multipart():
            return attachments

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue

            filename = part.get_filename()
            if not filename:
                continue

            # Decode filename
            filename = self._decode_header(filename)

            # Skip common signature images
            filename_lower = filename.lower()
            skip_patterns = ['image001', 'image002', 'logo', 'signature', 'banner']
            if any(p in filename_lower for p in skip_patterns):
                continue

            # Get size if available
            try:
                payload = part.get_payload(decode=True)
                size = len(payload) if payload else 0
            except (AttributeError, TypeError):
                size = 0

            attachments.append({
                'filename': filename,
                'content_type': part.get_content_type(),
                'size': size
            })

        return attachments


def main():
    """CLI entry point for testing."""
    print("=" * 70)
    print("SENT EMAIL PROPOSAL DETECTOR")
    print("=" * 70)

    detector = SentEmailDetector()

    if not detector.connect():
        print("Failed to connect to email server")
        return

    print("\nScanning Sent folder for proposal emails...")
    results = detector.scan_sent_for_proposals(days_back=30, limit=200)

    detector.close()

    print(f"\n{'=' * 70}")
    print("RESULTS:")
    print(f"  Emails scanned: {results['emails_scanned']}")
    print(f"  Proposals detected: {results['proposals_detected']}")
    print(f"  Suggestions created: {results['suggestions_created']}")

    if results['detections']:
        print(f"\nDETECTIONS:")
        for d in results['detections'][:10]:
            print(f"  - {d['matched_proposal']['project_code']}: {d['subject'][:50]}...")
            print(f"    Confidence: {d['confidence']:.2f}, Match: {d['matched_proposal']['match_type']}")

    if results['errors']:
        print(f"\nERRORS ({len(results['errors'])}):")
        for e in results['errors'][:5]:
            print(f"  - {e}")

    print(f"\n{'=' * 70}")
    print("Done! Check /admin/suggestions for new proposal status suggestions.")


if __name__ == '__main__':
    main()

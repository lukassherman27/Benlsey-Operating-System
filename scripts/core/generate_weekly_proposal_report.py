#!/usr/bin/env python3
"""
Automated Weekly Proposal Report Generator
Pulls data from proposal_tracker and generates PDF for Bill

Enhanced version includes:
- Transcript context (recent meeting notes per proposal)
- Contact info (key contacts per proposal)
- Email activity summary (last 5 emails per proposal)
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


def get_proposal_transcripts(cursor, proposal_id: int, limit: int = 3) -> list:
    """Get recent meeting transcripts for a proposal"""
    cursor.execute("""
        SELECT
            meeting_title,
            meeting_date,
            substr(summary, 1, 300) as summary,
            key_points,
            action_items,
            participants
        FROM meeting_transcripts
        WHERE proposal_id = ?
        ORDER BY meeting_date DESC, created_at DESC
        LIMIT ?
    """, (proposal_id, limit))
    return [dict(row) for row in cursor.fetchall()]


def get_proposal_contacts(cursor, proposal_id: int, limit: int = 5) -> list:
    """Get key contacts linked to a proposal"""
    cursor.execute("""
        SELECT
            c.name,
            c.email,
            c.company,
            c.role,
            pcl.role as link_role
        FROM project_contact_links pcl
        JOIN contacts c ON pcl.contact_id = c.contact_id
        WHERE pcl.proposal_id = ?
        ORDER BY pcl.confidence_score DESC, pcl.email_count DESC
        LIMIT ?
    """, (proposal_id, limit))
    return [dict(row) for row in cursor.fetchall()]


def get_proposal_emails(cursor, proposal_id: int, limit: int = 5) -> list:
    """Get recent emails linked to a proposal"""
    cursor.execute("""
        SELECT
            e.subject,
            e.date,
            e.sender_name,
            e.sender_email,
            substr(COALESCE(e.ai_summary, e.body_preview, ''), 1, 150) as preview
        FROM email_proposal_links epl
        JOIN emails e ON epl.email_id = e.email_id
        WHERE epl.proposal_id = ?
        ORDER BY e.date DESC
        LIMIT ?
    """, (proposal_id, limit))
    return [dict(row) for row in cursor.fetchall()]


def get_proposal_id_from_code(cursor, project_code: str) -> int:
    """Get proposal_id from project_code"""
    cursor.execute("""
        SELECT proposal_id FROM proposals WHERE project_code = ?
    """, (project_code,))
    row = cursor.fetchone()
    return row['proposal_id'] if row else None

def generate_weekly_report(output_path=None):
    """Generate weekly proposal overview PDF"""

    if not output_path:
        # Output to reports directory, create if needed
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        output_path = reports_dir / f"Bensley_Proposal_Overview_{datetime.now().strftime('%Y-%m-%d')}.pdf"

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all active proposals with email activity
    cursor.execute("""
        SELECT
            pt.project_code,
            pt.project_name,
            COALESCE(pt.project_value, 0) as project_value,
            pt.country,
            pt.current_status,
            COALESCE(pt.last_week_status, pt.current_status) as last_week_status,
            COALESCE(pt.days_in_current_status, 0) as days_in_current_status,
            CASE WHEN pt.proposal_sent = 1 THEN 'Yes' ELSE 'No' END as proposal_sent,
            COALESCE(pt.first_contact_date, '') as first_contact_date,
            COALESCE(pt.proposal_sent_date, '') as proposal_sent_date,
            COALESCE(pt.current_remark, '') as current_remark,
            COALESCE(email_stats.email_count, 0) as email_count,
            COALESCE(email_stats.last_email_date, '') as last_email_date
        FROM proposal_tracker pt
        LEFT JOIN proposals p ON pt.project_code = p.project_code
        LEFT JOIN (
            SELECT
                epl.proposal_id,
                COUNT(*) as email_count,
                MAX(e.date) as last_email_date
            FROM email_proposal_links epl
            JOIN emails e ON epl.email_id = e.email_id
            GROUP BY epl.proposal_id
        ) email_stats ON p.proposal_id = email_stats.proposal_id
        WHERE pt.is_active = 1
        ORDER BY pt.project_code
    """)

    proposals = cursor.fetchall()

    print(f"Generating report with {len(proposals)} active proposals...")

    # Color definitions
    COLOR_GREEN = colors.HexColor('#92D050')
    COLOR_BLUE = colors.HexColor('#00B0F0')
    COLOR_ORANGE = colors.HexColor('#FFC000')
    COLOR_RED = colors.HexColor('#FF0000')
    COLOR_HEADER = colors.HexColor('#1F4E78')

    # Create PDF
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=10*mm,
        leftMargin=10*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )

    elements = []

    # Title
    title_style = ParagraphStyle(
        'Title',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=COLOR_HEADER,
        alignment=TA_CENTER,
        spaceAfter=8
    )

    title = Paragraph("BENSLEY DESIGN STUDIOS - PROPOSAL OVERVIEW", title_style)
    date_para = Paragraph(
        f"<font name='Helvetica' size='9'>Updated: {datetime.now().strftime('%B %d, %Y')}</font>",
        ParagraphStyle('Date', alignment=TA_CENTER)
    )

    elements.append(title)
    elements.append(date_para)
    elements.append(Spacer(1, 5*mm))

    # Prepare table data
    data = [
        ['Project #', 'Project Name', 'Value', 'Last Week', 'Current Status',
         'Days', 'Sent?', 'Emails', 'Last Email', 'Remark', 'Country']
    ]

    for p in proposals:
        data.append([
            p['project_code'],
            p['project_name'][:30],  # Truncate long names
            f"${p['project_value']:,.0f}" if p['project_value'] > 0 else '$0',
            p['last_week_status'],
            p['current_status'],
            str(p['days_in_current_status']),
            p['proposal_sent'],
            str(p['email_count']) if p['email_count'] > 0 else '-',
            p['last_email_date'][:10] if p['last_email_date'] else '-',
            p['current_remark'][:50] if p['current_remark'] else '',  # Shorter remark
            p['country'][:12] if p['country'] else ''
        ])

    # Column widths
    col_widths = [
        18*mm,   # Project #
        42*mm,   # Project Name
        18*mm,   # Value
        18*mm,   # Last Week
        20*mm,   # Current Status
        10*mm,   # Days
        10*mm,   # Sent?
        12*mm,   # Emails
        18*mm,   # Last Email
        55*mm,   # Remark (shorter)
        14*mm,   # Country
    ]

    # Create table
    table = Table(data, colWidths=col_widths, repeatRows=1)

    # Table style
    table_style = TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Data cells
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (2, -1), 'LEFT'),
        ('ALIGN', (3, 1), (-1, -1), 'LEFT'),

        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),

        # White grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.white),

        # Word wrap
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ])

    # Color-code status columns
    for i in range(1, len(data)):
        current_status = data[i][4]

        if 'Proposal Sent' in current_status:
            bg_color = COLOR_GREEN
        elif 'Drafting' in current_status:
            bg_color = COLOR_BLUE
        elif 'First Contact' in current_status:
            bg_color = COLOR_ORANGE
        elif 'On Hold' in current_status:
            bg_color = COLOR_RED
        else:
            bg_color = colors.white

        # Apply to Last Week (col 3) and Current Status (col 4)
        table_style.add('BACKGROUND', (3, i), (4, i), bg_color)
        table_style.add('FONTNAME', (3, i), (4, i), 'Helvetica-Bold')

    table.setStyle(table_style)
    elements.append(table)

    # Summary section
    elements.append(Spacer(1, 8*mm))

    # Count by status
    proposal_sent_count = sum(1 for p in proposals if 'Proposal Sent' in p['current_status'])
    drafting_count = sum(1 for p in proposals if 'Drafting' in p['current_status'])
    first_contact_count = sum(1 for p in proposals if 'First Contact' in p['current_status'])
    on_hold_count = sum(1 for p in proposals if 'On Hold' in p['current_status'])

    # Calculate total value and email stats
    total_value = sum(p['project_value'] for p in proposals)
    total_emails = sum(p['email_count'] for p in proposals)
    proposals_with_emails = sum(1 for p in proposals if p['email_count'] > 0)

    # Summary table
    summary_data = [
        ['SUMMARY', '', '', ''],
        ['Total Active Proposals:', f'{len(proposals)}', 'Total Pipeline Value:', f'${total_value:,.0f}'],
        ['Proposals with Email Activity:', f'{proposals_with_emails}', 'Total Linked Emails:', f'{total_emails}'],
        ['', '', '', ''],
        ['BY STATUS:', 'Count', 'BY STATUS:', 'Count'],
        ['Proposal Sent (GREEN)', f'{proposal_sent_count}', 'Drafting (BLUE)', f'{drafting_count}'],
        ['First Contact (ORANGE)', f'{first_contact_count}', 'On Hold (RED)', f'{on_hold_count}'],
    ]

    summary_table = Table(summary_data, colWidths=[60*mm, 30*mm, 60*mm, 30*mm])

    summary_style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('SPAN', (0, 0), (-1, 0)),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Stats row
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 9),

        # Status header
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 9),
        ('BACKGROUND', (0, 3), (1, 3), COLOR_HEADER),
        ('BACKGROUND', (2, 3), (3, 3), COLOR_HEADER),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.white),

        # Status rows with color coding
        ('BACKGROUND', (0, 4), (1, 4), COLOR_GREEN),
        ('BACKGROUND', (2, 4), (3, 4), COLOR_BLUE),
        ('BACKGROUND', (0, 5), (1, 5), COLOR_ORANGE),
        ('BACKGROUND', (2, 5), (3, 5), COLOR_RED),

        ('FONTNAME', (0, 4), (-1, 5), 'Helvetica'),
        ('FONTSIZE', (0, 4), (-1, 5), 9),

        # All cells
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),

        # White grid
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ])

    summary_table.setStyle(summary_style)
    elements.append(summary_table)

    # ============================================================
    # DETAIL PAGES - Per-proposal context (transcripts, contacts, emails)
    # ============================================================

    # Define styles for detail pages
    detail_styles = {
        'section_header': ParagraphStyle(
            'SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=COLOR_HEADER,
            spaceAfter=4*mm,
            spaceBefore=6*mm
        ),
        'subsection': ParagraphStyle(
            'Subsection',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            spaceAfter=2*mm,
            spaceBefore=4*mm
        ),
        'body': ParagraphStyle(
            'Body',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            spaceAfter=2*mm
        ),
        'small': ParagraphStyle(
            'Small',
            fontName='Helvetica',
            fontSize=7,
            leading=9,
            textColor=colors.HexColor('#666666')
        )
    }

    # Count proposals with context data
    proposals_with_context = 0

    for p in proposals:
        project_code = p['project_code']
        proposal_id = get_proposal_id_from_code(cursor, project_code)

        if not proposal_id:
            continue

        # Fetch context data
        transcripts = get_proposal_transcripts(cursor, proposal_id, limit=3)
        contacts = get_proposal_contacts(cursor, proposal_id, limit=5)
        emails = get_proposal_emails(cursor, proposal_id, limit=5)

        # Only create detail page if there's meaningful context
        if not transcripts and not contacts and p['email_count'] == 0:
            continue

        proposals_with_context += 1

        # Page break for each proposal detail
        elements.append(PageBreak())

        # Proposal header
        header_text = f"<b>{project_code}</b> - {p['project_name']}"
        elements.append(Paragraph(header_text, detail_styles['section_header']))

        # Status and value line
        status_line = f"Status: <b>{p['current_status']}</b> | Value: <b>${p['project_value']:,.0f}</b> | Country: {p['country'] or 'N/A'}"
        elements.append(Paragraph(status_line, detail_styles['body']))
        elements.append(Spacer(1, 3*mm))

        # --- TRANSCRIPT SECTION ---
        if transcripts:
            elements.append(Paragraph("📝 Recent Meeting Transcripts", detail_styles['subsection']))

            for t in transcripts:
                meeting_title = t.get('meeting_title') or 'Untitled Meeting'
                meeting_date = t.get('meeting_date') or 'Unknown date'
                summary = t.get('summary') or 'No summary available'
                key_points = t.get('key_points') or ''
                action_items = t.get('action_items') or ''

                # Meeting header
                meeting_header = f"<b>{meeting_title}</b> ({meeting_date})"
                elements.append(Paragraph(meeting_header, detail_styles['body']))

                # Summary (truncate if needed)
                if summary:
                    summary_clean = summary.replace('\n', ' ').replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph(f"Summary: {summary_clean}", detail_styles['small']))

                # Key points (if available)
                if key_points:
                    kp_clean = str(key_points)[:200].replace('\n', ' ').replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph(f"Key Points: {kp_clean}", detail_styles['small']))

                # Action items (if available)
                if action_items:
                    ai_clean = str(action_items)[:200].replace('\n', ' ').replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph(f"Action Items: {ai_clean}", detail_styles['small']))

                elements.append(Spacer(1, 2*mm))
        else:
            elements.append(Paragraph("📝 Meeting Transcripts", detail_styles['subsection']))
            elements.append(Paragraph("No meeting transcripts linked to this proposal.", detail_styles['small']))

        # --- CONTACTS SECTION ---
        elements.append(Paragraph("👥 Key Contacts", detail_styles['subsection']))

        if contacts:
            contact_data = [['Name', 'Email', 'Company', 'Role']]
            for c in contacts:
                name = (c.get('name') or 'Unknown')[:30]
                email = (c.get('email') or '')[:35]
                company = (c.get('company') or '')[:20]
                role = c.get('link_role') or c.get('role') or ''
                contact_data.append([name, email, company, role[:15]])

            contact_table = Table(contact_data, colWidths=[50*mm, 70*mm, 45*mm, 30*mm])
            contact_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ]))
            elements.append(contact_table)
        else:
            elements.append(Paragraph("No contacts linked to this proposal.", detail_styles['small']))

        elements.append(Spacer(1, 3*mm))

        # --- EMAIL ACTIVITY SECTION ---
        elements.append(Paragraph(f"📧 Recent Email Activity ({p['email_count']} total)", detail_styles['subsection']))

        if emails:
            email_data = [['Date', 'From', 'Subject', 'Preview']]
            for e in emails:
                date_str = (e.get('date') or '')[:10]
                sender = (e.get('sender_name') or e.get('sender_email') or 'Unknown')[:20]
                subject = (e.get('subject') or 'No subject')[:40]
                preview = (e.get('preview') or '')[:60]
                # Clean preview for PDF
                preview = preview.replace('\n', ' ').replace('<', '&lt;').replace('>', '&gt;')
                email_data.append([date_str, sender, subject, preview])

            email_table = Table(email_data, colWidths=[22*mm, 35*mm, 60*mm, 80*mm])
            email_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ]))
            elements.append(email_table)
        else:
            elements.append(Paragraph("No emails linked to this proposal.", detail_styles['small']))

    print(f"  → Generating {proposals_with_context} proposal detail pages...")

    # Build PDF
    doc.build(elements)

    # Log report generation
    cursor.execute("""
        INSERT INTO weekly_proposal_reports (
            report_date, week_ending, pdf_path, proposals_count, total_pipeline_value
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d'),
        str(output_path),
        len(proposals),
        total_value
    ))

    conn.commit()
    conn.close()

    print(f"\n✓ Report generated: {output_path}")
    print(f"✓ Total proposals: {len(proposals)}")
    print(f"✓ Total pipeline: ${total_value:,.0f}")
    print(f"✓ Proposals with email activity: {proposals_with_emails}")
    print(f"✓ Total linked emails: {total_emails}")
    print(f"✓ Detail pages generated: {proposals_with_context}")

    return output_path


if __name__ == "__main__":
    generate_weekly_report()

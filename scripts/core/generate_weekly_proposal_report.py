#!/usr/bin/env python3
"""
Automated Weekly Proposal Report Generator
Pulls data from proposal_tracker and generates PDF for Bill
"""

import sqlite3
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

def generate_weekly_report(output_path=None):
    """Generate weekly proposal overview PDF"""

    if not output_path:
        output_path = f"/Users/lukassherman/Desktop/Bensley Proposal Overview ({datetime.now().strftime('%B %d')}).pdf"

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all active proposals
    cursor.execute("""
        SELECT
            project_code,
            project_name,
            COALESCE(project_value, 0) as project_value,
            country,
            current_status,
            COALESCE(last_week_status, current_status) as last_week_status,
            COALESCE(days_in_current_status, 0) as days_in_current_status,
            CASE WHEN proposal_sent = 1 THEN 'Yes' ELSE 'No' END as proposal_sent,
            COALESCE(first_contact_date, '') as first_contact_date,
            COALESCE(proposal_sent_date, '') as proposal_sent_date,
            COALESCE(current_remark, '') as current_remark
        FROM proposal_tracker
        WHERE is_active = 1
        ORDER BY project_code
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
        output_path,
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
         'Days', 'Sent?', 'First Contact', 'Proposal Date', 'Remark', 'Country']
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
            p['first_contact_date'][:10] if p['first_contact_date'] else '',
            p['proposal_sent_date'][:10] if p['proposal_sent_date'] else '',
            p['current_remark'][:80] if p['current_remark'] else '',  # Truncate
            p['country'][:15] if p['country'] else ''
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
        18*mm,   # First Contact
        18*mm,   # Proposal Date
        70*mm,   # Remark
        16*mm,   # Country
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

    # Calculate total value
    total_value = sum(p['project_value'] for p in proposals)

    # Summary table
    summary_data = [
        ['SUMMARY', '', '', ''],
        ['Total Active Proposals:', f'{len(proposals)}', 'Total Pipeline Value:', f'${total_value:,.0f}'],
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
        output_path,
        len(proposals),
        total_value
    ))

    conn.commit()
    conn.close()

    print(f"\n✓ Report generated: {output_path}")
    print(f"✓ Total proposals: {len(proposals)}")
    print(f"✓ Total pipeline: ${total_value:,.0f}")

    return output_path


if __name__ == "__main__":
    generate_weekly_report()

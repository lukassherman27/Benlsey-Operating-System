#!/usr/bin/env python3
"""
Schedule PDF Generator - Calendar Grid Format
Generates schedules matching the exact Bali/Bangkok format
"""

import sqlite3
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import os

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


class SchedulePDFGenerator:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.project_colors = {}

    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        # Load project colors
        cursor = self.conn.cursor()
        cursor.execute("SELECT project_title, color_hex FROM project_colors")
        for row in cursor.fetchall():
            self.project_colors[row['project_title']] = row['color_hex']

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def hex_to_rgb(self, hex_color: str):
        """Convert hex color to RGB tuple for ReportLab"""
        if not hex_color or not hex_color.startswith('#'):
            return colors.white
        hex_color = hex_color.lstrip('#')
        try:
            r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
            return colors.Color(r, g, b)
        except:
            return colors.white

    def get_project_color(self, project_title: str):
        """Get color for a project"""
        # Try exact match
        if project_title in self.project_colors:
            return self.hex_to_rgb(self.project_colors[project_title])

        # Try partial match
        for proj, color in self.project_colors.items():
            if proj.lower() in project_title.lower() or project_title.lower() in proj.lower():
                return self.hex_to_rgb(color)

        # Default colors
        default_colors = [
            colors.lightblue, colors.lightgreen, colors.lightyellow,
            colors.pink, colors.lavender, colors.lightcyan,
            colors.peachpuff, colors.lightgoldenrodyellow
        ]
        return default_colors[hash(project_title) % len(default_colors)]

    def generate_schedule_pdf(self, schedule_id: int, output_path: str):
        """Generate calendar-style PDF matching Bali/Bangkok format"""
        cursor = self.conn.cursor()

        # Get schedule details
        cursor.execute("""
            SELECT office, week_start_date, week_end_date
            FROM weekly_schedules
            WHERE schedule_id = ?
        """, (schedule_id,))
        schedule = cursor.fetchone()

        if not schedule:
            print(f"Schedule {schedule_id} not found")
            return False

        office = schedule['office']
        week_start = datetime.strptime(schedule['week_start_date'], "%Y-%m-%d")
        week_end = datetime.strptime(schedule['week_end_date'], "%Y-%m-%d")

        # Generate weekday dates
        weekdays = []
        current = week_start
        while current <= week_end:
            if current.weekday() < 5:  # Mon-Fri only
                weekdays.append(current)
            current += timedelta(days=1)

        # Get all team members and their assignments
        cursor.execute("""
            SELECT DISTINCT
                tm.member_id,
                tm.nickname,
                se.project_title,
                se.task_description,
                se.phase
            FROM schedule_entries se
            JOIN team_members tm ON se.member_id = tm.member_id
            WHERE se.schedule_id = ?
            ORDER BY tm.nickname
        """, (schedule_id,))

        members = {}
        for row in cursor.fetchall():
            member_id = row['member_id']
            if member_id not in members:
                members[member_id] = {
                    'nickname': row['nickname'],
                    'project': row['project_title'],
                    'task': row['task_description'],
                    'phase': row['phase']
                }

        if not members:
            print(f"No entries for schedule {schedule_id}")
            return False

        # Create PDF with tighter margins for single page
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(letter),
            rightMargin=0.25*inch,
            leftMargin=0.25*inch,
            topMargin=0.3*inch,
            bottomMargin=0.2*inch
        )

        styles = getSampleStyleSheet()
        content = []

        # Modern title with gradient-like effect
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=2
        )
        title = Paragraph(f"<b>{office} Team Schedule</b>", title_style)

        # Elegant subtitle
        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666'),
            spaceAfter=4
        )
        subtitle_text = f"{week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}"
        subtitle = Paragraph(subtitle_text, subtitle_style)

        content.append(title)
        content.append(subtitle)
        content.append(Spacer(1, 0.05*inch))

        # Build table data
        table_data = []

        # Header row 1: Day names
        day_row = ['NAME'] + [d.strftime('%a') for d in weekdays]
        table_data.append(day_row)

        # Header row 2: Dates
        date_row = [''] + [d.strftime('%d') for d in weekdays]
        table_data.append(date_row)

        # Data rows: Each team member
        row_colors = []
        cell_spans = []  # Track cells to span
        row_idx = 2  # Start after headers

        for member_id, member_info in members.items():
            name = member_info['nickname']
            project = member_info['project']
            task = member_info['task'] or ''
            phase = member_info['phase'] or ''

            # Create project text
            project_text = f"{project}"
            if task:
                project_text += f"\n{task}"
            if phase:
                project_text += f" - {phase}"

            # Name cell with better styling
            name_para = Paragraph(f"<font size=8><b>{name}</b></font>", styles['Normal'])

            # Project cell - clean, readable text
            project_para = Paragraph(f"<font size=7.5>{project_text}</font>", styles['Normal'])

            # Create row with name + first project cell + empty cells
            row = [name_para, project_para] + [''] * (len(weekdays) - 1)
            table_data.append(row)

            # Span the project cell across all weekday columns
            start_col = 1
            end_col = len(weekdays)
            cell_spans.append(('SPAN', (start_col, row_idx), (end_col, row_idx)))

            # Color the entire spanned cell
            project_color = self.get_project_color(project)
            row_colors.append(('BACKGROUND', (start_col, row_idx), (end_col, row_idx), project_color))

            row_idx += 1

        # Calculate column widths - optimize for single page
        name_col_width = 0.9 * inch
        day_col_width = (10.0 * inch) / len(weekdays)  # Distribute remaining space
        col_widths = [name_col_width] + [day_col_width] * len(weekdays)

        # Create table
        table = Table(table_data, colWidths=col_widths, repeatRows=2)

        # Modern, clean table style
        table_style = TableStyle([
            # Modern header with darker shade
            ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 1), 8),
            ('TOPPADDING', (0, 0), (-1, 1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, 1), 5),

            # Name column styling
            ('ALIGN', (0, 2), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 2), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (0, -1), 9),
            ('LEFTPADDING', (0, 2), (0, -1), 6),
            ('BACKGROUND', (0, 2), (0, -1), colors.HexColor('#f8f9fa')),

            # Clean grid with subtle lines
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#2c3e50')),
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.HexColor('#2c3e50')),
            ('GRID', (0, 2), (-1, -1), 0.3, colors.HexColor('#dee2e6')),
            ('BOX', (0, 0), (-1, -1), 1.2, colors.HexColor('#2c3e50')),

            # Ultra-compact padding for single page
            ('TOPPADDING', (0, 2), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 2), (-1, -1), 2),
            ('LEFTPADDING', (1, 2), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ])

        # Add cell spans first (before colors)
        for span_spec in cell_spans:
            table_style.add(*span_spec)

        # Add project colors
        for color_spec in row_colors:
            table_style.add(*color_spec)

        table.setStyle(table_style)
        content.append(table)

        # Build PDF
        doc.build(content)
        print(f"PDF generated: {output_path}")

        # Update database
        cursor.execute("""
            UPDATE weekly_schedules
            SET pdf_path = ?, pdf_generated = 1, updated_at = datetime('now')
            WHERE schedule_id = ?
        """, (output_path, schedule_id))
        self.conn.commit()

        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 schedule_pdf_generator.py <schedule_id> [output_path]")
        sys.exit(1)

    schedule_id = int(sys.argv[1])
    output_path = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/Bensley_Schedule_{schedule_id}.pdf"

    generator = SchedulePDFGenerator()
    generator.connect()

    try:
        success = generator.generate_schedule_pdf(schedule_id, output_path)
        if success:
            print(f"\n✅ PDF generated successfully!")
            print(f"Location: {output_path}")
        else:
            print("\n❌ Failed to generate PDF")
    finally:
        generator.close()


if __name__ == "__main__":
    main()

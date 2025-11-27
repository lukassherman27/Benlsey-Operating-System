#!/usr/bin/env python3
"""
Send beautiful HTML project status report email
"""

import sqlite3
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Load .env file
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

def get_project_data(project_identifier: str):
    """Get all project data for the report"""
    from datetime import timedelta

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find project - include contract dates
    search_words = project_identifier.split()
    if len(search_words) == 1:
        cursor.execute("""
            SELECT project_id, project_code, project_title, status, total_fee_usd, country,
                   contract_start_date, contract_expiry_date, payment_terms_days
            FROM projects
            WHERE project_code LIKE ? OR project_title LIKE ?
            LIMIT 1
        """, (f"%{project_identifier}%", f"%{project_identifier}%"))
    else:
        conditions = " AND ".join([f"project_title LIKE ?" for _ in search_words])
        params = [f"%{word}%" for word in search_words]
        cursor.execute(f"""
            SELECT project_id, project_code, project_title, status, total_fee_usd, country,
                   contract_start_date, contract_expiry_date, payment_terms_days
            FROM projects
            WHERE ({conditions})
            LIMIT 1
        """, params)

    project = dict(cursor.fetchone())
    project_code = project['project_code']
    project_id = project['project_id']

    # Get fee breakdown by scope
    cursor.execute("""
        SELECT scope, discipline, phase, phase_fee_usd, total_invoiced, total_paid, breakdown_id
        FROM project_fee_breakdown
        WHERE project_code = ?
        ORDER BY scope,
            CASE phase
                WHEN 'Mobilization' THEN 1
                WHEN 'Concept Design' THEN 2
                WHEN 'Design Development' THEN 3
                WHEN 'Construction Documents' THEN 4
                WHEN 'Construction Observation' THEN 5
                ELSE 6
            END
    """, (project_code,))
    breakdown_rows = [dict(r) for r in cursor.fetchall()]

    # Get invoices
    cursor.execute("""
        SELECT
            i.invoice_number, i.description, i.invoice_amount, i.invoice_date,
            i.payment_amount, i.payment_date, i.status, b.scope, b.phase
        FROM invoices i
        LEFT JOIN project_fee_breakdown b ON i.breakdown_id = b.breakdown_id
        WHERE i.project_id = ?
        ORDER BY i.invoice_date
    """, (project_id,))
    invoices = [dict(r) for r in cursor.fetchall()]

    # Get reimbursable expenses
    cursor.execute("""
        SELECT expense_id, invoice_number, invoice_date, description, category,
               trip_destination, travelers, amount_invoiced, amount_paid, date_paid, status
        FROM reimbursable_expenses
        WHERE project_code = ?
        ORDER BY invoice_date DESC
    """, (project_code,))
    reimbursables = [dict(r) for r in cursor.fetchall()]

    # Calculate reimbursables totals
    reimbursables_invoiced = sum(r['amount_invoiced'] or 0 for r in reimbursables)
    reimbursables_paid = sum(r['amount_paid'] or 0 for r in reimbursables)
    reimbursables_outstanding = reimbursables_invoiced - reimbursables_paid

    # Get recently paid invoices (last 60 days)
    cursor.execute("""
        SELECT i.invoice_number, i.invoice_amount, i.payment_amount, i.payment_date, b.scope, b.phase
        FROM invoices i
        LEFT JOIN project_fee_breakdown b ON i.breakdown_id = b.breakdown_id
        WHERE i.project_id = ? AND i.payment_date IS NOT NULL
          AND i.payment_date >= date('now', '-60 days')
        ORDER BY i.payment_date DESC
        LIMIT 5
    """, (project_id,))
    recently_paid = [dict(r) for r in cursor.fetchall()]

    # Get recently issued invoices not yet paid (within payment terms - not overdue)
    payment_terms = project.get('payment_terms_days') or 30
    cursor.execute(f"""
        SELECT i.invoice_number, i.invoice_amount, i.invoice_date, b.scope, b.phase,
               julianday('now') - julianday(i.invoice_date) as days_since_issued
        FROM invoices i
        LEFT JOIN project_fee_breakdown b ON i.breakdown_id = b.breakdown_id
        WHERE i.project_id = ?
          AND (i.payment_date IS NULL OR i.payment_amount < i.invoice_amount)
          AND julianday('now') - julianday(i.invoice_date) <= ?
        ORDER BY i.invoice_date DESC
        LIMIT 5
    """, (project_id, payment_terms))
    recently_issued_pending = [dict(r) for r in cursor.fetchall()]

    # Get recently paid reimbursables (last 60 days)
    cursor.execute("""
        SELECT invoice_number, description, amount_invoiced, amount_paid, date_paid, category
        FROM reimbursable_expenses
        WHERE project_code = ? AND date_paid IS NOT NULL
          AND date_paid >= date('now', '-60 days')
        ORDER BY date_paid DESC
        LIMIT 5
    """, (project_code,))
    recently_paid_reimbursables = [dict(r) for r in cursor.fetchall()]

    conn.close()

    # Organize by scope
    scopes = {}
    for row in breakdown_rows:
        scope = row['scope'] or 'unassigned'
        if scope not in scopes:
            scopes[scope] = {
                'scope': scope,
                'discipline': row['discipline'],
                'phases': [],
                'contract_total': 0,
                'invoiced_total': 0,
                'paid_total': 0
            }
        phase_data = {
            'phase': row['phase'],
            'contract_fee': row['phase_fee_usd'] or 0,
            'invoiced': row['total_invoiced'] or 0,
            'paid': row['total_paid'] or 0,
            'breakdown_id': row['breakdown_id']
        }
        scopes[scope]['phases'].append(phase_data)
        scopes[scope]['contract_total'] += phase_data['contract_fee']
        scopes[scope]['invoiced_total'] += phase_data['invoiced']
        scopes[scope]['paid_total'] += phase_data['paid']

    # Build invoice lookup
    invoices_by_scope_phase = {}
    for inv in invoices:
        key = (inv.get('scope') or 'unassigned', inv.get('phase') or 'unassigned')
        if key not in invoices_by_scope_phase:
            invoices_by_scope_phase[key] = []
        invoices_by_scope_phase[key].append(inv)

    # Calculate totals
    total_contract = project['total_fee_usd'] or sum(s['contract_total'] for s in scopes.values())
    total_invoiced = sum(s['invoiced_total'] for s in scopes.values())
    total_paid = sum(s['paid_total'] for s in scopes.values())
    total_outstanding = total_invoiced - total_paid

    # Outstanding invoices
    outstanding = [inv for inv in invoices if inv['status'] == 'outstanding' or not inv.get('payment_date')]

    return {
        'project': project,
        'scopes': scopes,
        'invoices_by_scope_phase': invoices_by_scope_phase,
        'totals': {
            'contract': total_contract,
            'invoiced': total_invoiced,
            'paid': total_paid,
            'outstanding': total_outstanding,
            'remaining': total_contract - total_invoiced
        },
        'outstanding_invoices': outstanding,
        'reimbursables': {
            'items': reimbursables,
            'invoiced': reimbursables_invoiced,
            'paid': reimbursables_paid,
            'outstanding': reimbursables_outstanding
        },
        'recent_activity': {
            'recently_paid': recently_paid,
            'recently_issued_pending': recently_issued_pending,
            'recently_paid_reimbursables': recently_paid_reimbursables
        }
    }


def generate_html_email(data: dict) -> str:
    """Generate beautiful HTML email"""
    project = data['project']
    scopes = data['scopes']
    totals = data['totals']
    outstanding = data['outstanding_invoices']
    invoices_by_scope_phase = data['invoices_by_scope_phase']
    reimbursables = data.get('reimbursables', {'items': [], 'invoiced': 0, 'paid': 0, 'outstanding': 0})
    recent_activity = data.get('recent_activity', {'recently_paid': [], 'recently_issued_pending': [], 'recently_paid_reimbursables': []})

    # Calculate some extra stats
    num_scopes = len([s for s in scopes.values() if 'additional' not in s['scope'].lower()])
    collection_rate = (totals['paid']/totals['invoiced']*100) if totals['invoiced'] > 0 else 0
    invoice_rate = (totals['invoiced']/totals['contract']*100) if totals['contract'] > 0 else 0

    # Contract dates
    contract_start = project.get('contract_start_date') or 'N/A'
    contract_end = project.get('contract_expiry_date') or 'Ongoing'

    # Grand totals including reimbursables
    grand_total_outstanding = totals['outstanding'] + reimbursables['outstanding']

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: #f0f4f8;
            margin: 0;
            padding: 30px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 950px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            overflow: hidden;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0c4a6e 100%);
            color: white;
            padding: 40px 50px;
            position: relative;
        }}
        .header::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #06b6d4, #3b82f6, #8b5cf6);
        }}
        .header h1 {{
            margin: 0 0 12px 0;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .header-meta {{
            opacity: 0.85;
            font-size: 15px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .header-meta span {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        /* Big Numbers Summary */
        .hero-summary {{
            background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
            padding: 40px 50px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .hero-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 30px;
            margin-bottom: 30px;
        }}
        .hero-item {{
            text-align: center;
            padding: 25px 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            border: 1px solid #e2e8f0;
        }}
        .hero-item.highlight {{
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border-color: #6ee7b7;
        }}
        .hero-item.warning {{
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            border-color: #fca5a5;
        }}
        .hero-item.info {{
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border-color: #93c5fd;
        }}
        .hero-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #64748b;
            margin-bottom: 12px;
            font-weight: 600;
        }}
        .hero-value {{
            font-size: 36px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -1px;
        }}
        .hero-item.highlight .hero-value {{
            color: #059669;
        }}
        .hero-item.warning .hero-value {{
            color: #dc2626;
        }}
        .hero-item.info .hero-value {{
            color: #2563eb;
        }}
        .hero-subtitle {{
            font-size: 12px;
            color: #94a3b8;
            margin-top: 8px;
        }}

        /* Progress bars - table based for email */
        .progress-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 15px 0;
        }}
        .progress-item {{
            background: white;
            padding: 20px 25px;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            width: 50%;
        }}
        .progress-label {{
            font-size: 13px;
            font-weight: 600;
            color: #475569;
            display: block;
            margin-bottom: 8px;
        }}
        .progress-value {{
            font-size: 13px;
            font-weight: 700;
            color: #0f172a;
            display: block;
            margin-bottom: 12px;
        }}
        .progress-bar-outer {{
            height: 12px;
            background: #e2e8f0;
            border-radius: 6px;
            width: 100%;
        }}
        .progress-bar-fill {{
            height: 12px;
            border-radius: 6px;
        }}
        .progress-bar-fill.green {{
            background-color: #10b981;
        }}
        .progress-bar-fill.blue {{
            background-color: #3b82f6;
        }}

        /* Scope sections */
        .scope-section {{
            border-bottom: 1px solid #e2e8f0;
        }}
        .scope-section.has-outstanding {{
            border-left: 4px solid #ef4444;
        }}
        .scope-header {{
            background: #f8fafc;
            padding: 25px 50px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .scope-title {{
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .scope-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }}
        .scope-icon.restaurant {{ background: linear-gradient(135deg, #fef3c7, #fde68a); }}
        .scope-icon.club {{ background: linear-gradient(135deg, #e0e7ff, #c7d2fe); }}
        .scope-icon.services {{ background: linear-gradient(135deg, #f3e8ff, #e9d5ff); }}
        .scope-subtitle {{
            font-size: 13px;
            color: #64748b;
            margin-top: 4px;
            margin-left: 52px;
        }}
        .scope-totals {{
            text-align: right;
        }}
        .scope-amount {{
            font-size: 24px;
            font-weight: 700;
            color: #0f172a;
        }}
        .scope-outstanding-badge {{
            display: inline-block;
            background: #fef2f2;
            color: #dc2626;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 20px;
            margin-top: 6px;
        }}

        /* Phase sections */
        .phase-section {{
            padding: 25px 50px;
            border-top: 1px solid #f1f5f9;
        }}
        .phase-section.has-outstanding {{
            background: #fffbeb;
        }}
        .phase-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .phase-title {{
            font-size: 16px;
            font-weight: 600;
            color: #334155;
        }}
        .phase-fee {{
            font-size: 15px;
            color: #64748b;
            font-weight: 500;
        }}
        .phase-fee strong {{
            color: #1e293b;
        }}

        /* Invoice table */
        .invoice-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 14px;
            margin-bottom: 20px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }}
        .invoice-table th {{
            background: #f1f5f9;
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            color: #475569;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .invoice-table td {{
            padding: 16px;
            border-top: 1px solid #f1f5f9;
            color: #334155;
        }}
        .invoice-table tr:hover td {{
            background: #f8fafc;
        }}
        .invoice-table tr.outstanding td {{
            background: #fef2f2;
        }}
        .invoice-table tr.outstanding:hover td {{
            background: #fee2e2;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .status-badge.paid {{
            background: #dcfce7;
            color: #166534;
        }}
        .status-badge.pending {{
            background: #fef3c7;
            color: #92400e;
        }}
        .status-badge.outstanding {{
            background: #fee2e2;
            color: #dc2626;
        }}

        /* Phase summary - table based for email */
        .phase-summary {{
            padding: 16px 20px;
            background: #f8fafc;
            border-radius: 8px;
            font-size: 14px;
        }}
        .phase-summary.warning {{
            background: #fef2f2;
            border: 1px solid #fecaca;
        }}
        .phase-summary-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .phase-summary-table td {{
            padding: 8px 20px 8px 0;
            white-space: nowrap;
        }}
        .phase-summary-label {{
            color: #64748b;
            padding-right: 8px;
        }}
        .phase-summary-value {{
            font-weight: 700;
            color: #1e293b;
        }}
        .phase-summary-value.red {{
            color: #dc2626;
        }}
        .phase-summary-value.green {{
            color: #16a34a;
        }}

        /* Outstanding section */
        .outstanding-section {{
            background: linear-gradient(135deg, #fef2f2 0%, #fff1f2 100%);
            padding: 40px 50px;
            border-top: 3px solid #ef4444;
        }}
        .outstanding-title {{
            color: #991b1b;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .outstanding-title span {{
            font-size: 24px;
        }}
        .outstanding-item {{
            background: white;
            padding: 20px 25px;
            border-radius: 12px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid #fecaca;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
        }}
        .outstanding-details {{
            font-size: 15px;
        }}
        .outstanding-invoice {{
            font-weight: 700;
            color: #1e293b;
            font-size: 16px;
        }}
        .outstanding-scope {{
            color: #64748b;
            font-size: 13px;
            margin-top: 6px;
        }}
        .outstanding-amount {{
            font-size: 24px;
            font-weight: 800;
            color: #dc2626;
        }}
        .outstanding-total {{
            margin-top: 25px;
            padding: 25px;
            background: white;
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 2px solid #ef4444;
        }}
        .outstanding-total-label {{
            font-size: 16px;
            font-weight: 700;
            color: #991b1b;
        }}
        .outstanding-total-value {{
            font-size: 32px;
            font-weight: 800;
            color: #dc2626;
        }}

        /* Footer */
        .footer {{
            padding: 25px 50px;
            background: #f8fafc;
            text-align: center;
            color: #64748b;
            font-size: 13px;
            border-top: 1px solid #e2e8f0;
        }}

        .no-invoices {{
            color: #94a3b8;
            font-style: italic;
            padding: 15px 0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>{project['project_title']}</h1>
            <div class="header-meta">
                <span>📋 {project['project_code']}</span>
                <span>🟢 {project['status']}</span>
                <span>📍 {project['country'] or 'N/A'}</span>
                <span>📅 Start: {contract_start}</span>
            </div>
        </div>

        <!-- Hero Summary - Big Numbers (Table Layout for Email) -->
        <div class="hero-summary" style="background:linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); padding:40px 50px; border-bottom:1px solid #e2e8f0;">
            <table cellpadding="0" cellspacing="0" style="width:100%; margin-bottom:30px;">
                <tr>
                    <td style="width:32%; text-align:center; padding:25px 20px; background:white; border-radius:12px; border:1px solid #e2e8f0;">
                        <div style="font-size:11px; text-transform:uppercase; letter-spacing:1.5px; color:#64748b; margin-bottom:12px; font-weight:600;">Contract Value</div>
                        <div style="font-size:36px; font-weight:800; color:#0f172a; letter-spacing:-1px;">${totals['contract']:,.0f}</div>
                        <div style="font-size:12px; color:#94a3b8; margin-top:8px;">Total project value</div>
                    </td>
                    <td style="width:2%;"></td>
                    <td style="width:32%; text-align:center; padding:25px 20px; background:linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-radius:12px; border:1px solid #6ee7b7;">
                        <div style="font-size:11px; text-transform:uppercase; letter-spacing:1.5px; color:#64748b; margin-bottom:12px; font-weight:600;">Total Collected</div>
                        <div style="font-size:36px; font-weight:800; color:#059669; letter-spacing:-1px;">${totals['paid']:,.0f}</div>
                        <div style="font-size:12px; color:#94a3b8; margin-top:8px;">{collection_rate:.1f}% collection rate</div>
                    </td>
                    <td style="width:2%;"></td>
                    <td style="width:32%; text-align:center; padding:25px 20px; background:{'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)' if totals['outstanding'] > 0 else 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)'}; border-radius:12px; border:1px solid {'#fca5a5' if totals['outstanding'] > 0 else '#93c5fd'};">
                        <div style="font-size:11px; text-transform:uppercase; letter-spacing:1.5px; color:#64748b; margin-bottom:12px; font-weight:600;">{'⚠️ Outstanding' if totals['outstanding'] > 0 else 'Outstanding'}</div>
                        <div style="font-size:36px; font-weight:800; color:{'#dc2626' if totals['outstanding'] > 0 else '#2563eb'}; letter-spacing:-1px;">${totals['outstanding']:,.0f}</div>
                        <div style="font-size:12px; color:#94a3b8; margin-top:8px;">{len(outstanding)} invoice{'s' if len(outstanding) != 1 else ''} pending</div>
                    </td>
                </tr>
            </table>

            <!-- Progress Bars - Table Layout for Email -->
            <table class="progress-table" cellpadding="0" cellspacing="0">
                <tr>
                    <td class="progress-item" style="background:white; padding:20px 25px; border:1px solid #e2e8f0; border-radius:10px;">
                        <span class="progress-label">Invoiced Progress</span>
                        <span class="progress-value">${totals['invoiced']:,.0f} / ${totals['contract']:,.0f} ({invoice_rate:.0f}%)</span>
                        <table class="progress-bar-outer" cellpadding="0" cellspacing="0" style="width:100%; background:#e2e8f0; border-radius:6px;">
                            <tr>
                                <td class="progress-bar-fill blue" style="width:{min(invoice_rate, 100)}%; height:12px; background-color:#3b82f6; border-radius:6px;"></td>
                                <td style="width:{100 - min(invoice_rate, 100)}%;"></td>
                            </tr>
                        </table>
                    </td>
                    <td style="width:15px;"></td>
                    <td class="progress-item" style="background:white; padding:20px 25px; border:1px solid #e2e8f0; border-radius:10px;">
                        <span class="progress-label">Collection Progress</span>
                        <span class="progress-value">${totals['paid']:,.0f} / ${totals['invoiced']:,.0f} ({collection_rate:.0f}%)</span>
                        <table class="progress-bar-outer" cellpadding="0" cellspacing="0" style="width:100%; background:#e2e8f0; border-radius:6px;">
                            <tr>
                                <td class="progress-bar-fill green" style="width:{min(collection_rate, 100)}%; height:12px; background-color:#10b981; border-radius:6px;"></td>
                                <td style="width:{100 - min(collection_rate, 100)}%;"></td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>
"""

    # Recent Activity Section (if there's any recent activity)
    recently_paid = recent_activity.get('recently_paid', [])
    recently_issued = recent_activity.get('recently_issued_pending', [])

    if recently_paid or recently_issued:
        html += """
        <!-- Recent Activity Section -->
        <div style="padding:30px 50px; background:#f8fafc; border-bottom:1px solid #e2e8f0;">
            <div style="font-size:18px; font-weight:700; color:#1e293b; margin-bottom:20px;">📊 Recent Activity</div>
            <table cellpadding="0" cellspacing="0" style="width:100%;">
                <tr>
"""
        # Recently Paid column
        html += """
                    <td style="width:48%; vertical-align:top; padding-right:20px;">
                        <div style="font-size:14px; font-weight:600; color:#16a34a; margin-bottom:12px;">✅ Recently Paid (Last 60 Days)</div>
"""
        if recently_paid:
            for inv in recently_paid:
                html += f"""
                        <div style="background:white; padding:12px 15px; border-radius:8px; margin-bottom:8px; border:1px solid #e2e8f0;">
                            <div style="font-weight:600; color:#1e293b;">{inv.get('invoice_number', 'N/A')}</div>
                            <div style="font-size:12px; color:#64748b;">{(inv.get('scope') or 'N/A').replace('-', ' ').title()} / {inv.get('phase', 'N/A')}</div>
                            <div style="font-size:14px; color:#16a34a; font-weight:700; margin-top:4px;">${inv.get('payment_amount', 0):,.2f}</div>
                            <div style="font-size:11px; color:#94a3b8;">Paid: {inv.get('payment_date', 'N/A')[:10] if inv.get('payment_date') else 'N/A'}</div>
                        </div>
"""
        else:
            html += '<div style="color:#94a3b8; font-style:italic;">No recent payments</div>'
        html += "</td>"

        # Recently Issued (Pending) column
        html += """
                    <td style="width:4%;"></td>
                    <td style="width:48%; vertical-align:top;">
                        <div style="font-size:14px; font-weight:600; color:#f59e0b; margin-bottom:12px;">⏳ Issued & Awaiting Payment</div>
"""
        if recently_issued:
            for inv in recently_issued:
                days = int(inv.get('days_since_issued', 0))
                html += f"""
                        <div style="background:#fffbeb; padding:12px 15px; border-radius:8px; margin-bottom:8px; border:1px solid #fde68a;">
                            <div style="font-weight:600; color:#1e293b;">{inv.get('invoice_number', 'N/A')}</div>
                            <div style="font-size:12px; color:#64748b;">{(inv.get('scope') or 'N/A').replace('-', ' ').title()} / {inv.get('phase', 'N/A')}</div>
                            <div style="font-size:14px; color:#f59e0b; font-weight:700; margin-top:4px;">${inv.get('invoice_amount', 0):,.2f}</div>
                            <div style="font-size:11px; color:#94a3b8;">Issued: {inv.get('invoice_date', 'N/A')[:10] if inv.get('invoice_date') else 'N/A'} ({days} days ago)</div>
                        </div>
"""
        else:
            html += '<div style="color:#94a3b8; font-style:italic;">No pending invoices within payment terms</div>'
        html += """
                    </td>
                </tr>
            </table>
        </div>
"""

    # Scope sections
    for scope_name, scope_data in scopes.items():
        scope_title = scope_name.replace('-', ' ').title()
        scope_outstanding = scope_data['invoiced_total'] - scope_data['paid_total']

        # Determine icon based on scope name
        if 'restaurant' in scope_name.lower() or 'brasserie' in scope_name.lower():
            icon_class = 'restaurant'
            icon = '🍽️'
        elif 'club' in scope_name.lower():
            icon_class = 'club'
            icon = '🎵'
        else:
            icon_class = 'services'
            icon = '⚙️'

        html += f"""
        <!-- {scope_title} -->
        <div class="scope-section {'has-outstanding' if scope_outstanding > 0 else ''}">
            <div class="scope-header">
                <div>
                    <div class="scope-title">
                        <div class="scope-icon {icon_class}">{icon}</div>
                        {scope_title}
                    </div>
                    <div class="scope-subtitle">{scope_data['discipline']}</div>
                </div>
                <div class="scope-totals">
                    <div class="scope-amount">${scope_data['contract_total']:,.0f}</div>
                    {'<div class="scope-outstanding-badge">⚠️ ${:,.0f} Outstanding</div>'.format(scope_outstanding) if scope_outstanding > 0 else ''}
                </div>
            </div>
"""

        for phase_data in scope_data['phases']:
            phase_name = phase_data['phase']
            phase_fee = phase_data['contract_fee']
            phase_invoiced = phase_data['invoiced']
            phase_paid = phase_data['paid']
            phase_outstanding = phase_invoiced - phase_paid
            phase_remaining = phase_fee - phase_invoiced

            phase_invoices = invoices_by_scope_phase.get((scope_name, phase_name), [])
            has_outstanding_invoice = any(not inv.get('payment_date') for inv in phase_invoices)

            html += f"""
            <div class="phase-section {'has-outstanding' if has_outstanding_invoice else ''}">
                <div class="phase-header">
                    <div class="phase-title">📌 {phase_name}</div>
                    <div class="phase-fee">Phase Fee: <strong>${phase_fee:,.0f}</strong></div>
                </div>
"""

            if phase_invoices:
                html += """
                <table class="invoice-table">
                    <thead>
                        <tr>
                            <th>Invoice #</th>
                            <th>Invoice Date</th>
                            <th>Amount</th>
                            <th>% of Phase</th>
                            <th>Paid</th>
                            <th>Paid Date</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
"""
                for inv in phase_invoices:
                    inv_amt = inv.get('invoice_amount') or 0
                    pct = (inv_amt / phase_fee * 100) if phase_fee > 0 else 0
                    paid_amt = inv.get('payment_amount') or 0
                    paid_date = inv.get('payment_date', '')[:10] if inv.get('payment_date') else '—'
                    is_paid = paid_amt >= inv_amt
                    is_outstanding = not inv.get('payment_date')

                    status_class = 'paid' if is_paid else ('outstanding' if is_outstanding else 'pending')
                    status_text = 'Paid ✓' if is_paid else ('Outstanding' if is_outstanding else 'Pending')

                    html += f"""
                        <tr class="{'outstanding' if is_outstanding else ''}">
                            <td><strong>{inv.get('invoice_number', 'N/A')}</strong></td>
                            <td>{inv.get('invoice_date', 'N/A')[:10] if inv.get('invoice_date') else 'N/A'}</td>
                            <td><strong>${inv_amt:,.2f}</strong></td>
                            <td>{pct:.0f}%</td>
                            <td>${paid_amt:,.2f}</td>
                            <td>{paid_date}</td>
                            <td><span class="status-badge {status_class}">{status_text}</span></td>
                        </tr>
"""
                html += """
                    </tbody>
                </table>
"""
            else:
                html += '<div class="no-invoices">No invoices yet for this phase</div>'

            # Phase summary - table layout for email compatibility
            warning_style = "background:#fef2f2; border:1px solid #fecaca;" if phase_outstanding > 0 else "background:#f8fafc;"
            html += f"""
                <div class="phase-summary" style="{warning_style} padding:16px 20px; border-radius:8px; font-size:14px;">
                    <table class="phase-summary-table" cellpadding="0" cellspacing="0" style="width:100%;">
                        <tr>
                            <td style="padding:8px 30px 8px 0;">
                                <span style="color:#64748b;">Invoiced:</span>
                                <span style="font-weight:700; color:#1e293b; margin-left:8px;">${phase_invoiced:,.0f}</span>
                            </td>
                            <td style="padding:8px 30px 8px 0;">
                                <span style="color:#64748b;">Collected:</span>
                                <span style="font-weight:700; color:#16a34a; margin-left:8px;">${phase_paid:,.0f}</span>
                            </td>
                            <td style="padding:8px 30px 8px 0;">
                                <span style="color:#64748b;">Outstanding:</span>
                                <span style="font-weight:700; color:{'#dc2626' if phase_outstanding > 0 else '#1e293b'}; margin-left:8px;">${phase_outstanding:,.0f}</span>
                            </td>
                            <td style="padding:8px 0;">
                                <span style="color:#64748b;">Remaining Fee:</span>
                                <span style="font-weight:700; color:#1e293b; margin-left:8px;">${phase_remaining:,.0f}</span>
                            </td>
                        </tr>
                    </table>
                </div>
            </div>
"""

        html += "</div>"  # Close scope section

    # Reimbursable Expenses Section
    if reimbursables['items']:
        reimb_items = reimbursables['items']
        reimb_outstanding_items = [r for r in reimb_items if r['status'] == 'outstanding']
        reimb_paid_items = [r for r in reimb_items if r['status'] == 'paid']

        html += f"""
        <!-- Reimbursable Expenses Section -->
        <div style="padding:30px 50px; background:#faf5ff; border-bottom:1px solid #e2e8f0;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <div style="font-size:20px; font-weight:700; color:#1e293b;">✈️ Reimbursable Expenses</div>
            </div>

            <!-- Reimbursables Summary -->
            <table cellpadding="0" cellspacing="0" style="width:100%; margin-bottom:20px;">
                <tr>
                    <td style="width:32%; text-align:center; padding:20px; background:white; border-radius:10px; border:1px solid #e2e8f0;">
                        <div style="font-size:11px; text-transform:uppercase; color:#64748b; margin-bottom:8px;">Total Invoiced</div>
                        <div style="font-size:24px; font-weight:700; color:#1e293b;">${reimbursables['invoiced']:,.2f}</div>
                    </td>
                    <td style="width:2%;"></td>
                    <td style="width:32%; text-align:center; padding:20px; background:#ecfdf5; border-radius:10px; border:1px solid #6ee7b7;">
                        <div style="font-size:11px; text-transform:uppercase; color:#64748b; margin-bottom:8px;">Total Paid</div>
                        <div style="font-size:24px; font-weight:700; color:#059669;">${reimbursables['paid']:,.2f}</div>
                    </td>
                    <td style="width:2%;"></td>
                    <td style="width:32%; text-align:center; padding:20px; background:{'#fef2f2' if reimbursables['outstanding'] > 0 else '#eff6ff'}; border-radius:10px; border:1px solid {'#fca5a5' if reimbursables['outstanding'] > 0 else '#93c5fd'};">
                        <div style="font-size:11px; text-transform:uppercase; color:#64748b; margin-bottom:8px;">Outstanding</div>
                        <div style="font-size:24px; font-weight:700; color:{'#dc2626' if reimbursables['outstanding'] > 0 else '#2563eb'};">${reimbursables['outstanding']:,.2f}</div>
                    </td>
                </tr>
            </table>
"""

        # Outstanding Reimbursables
        if reimb_outstanding_items:
            html += """
            <div style="margin-bottom:20px;">
                <div style="font-size:14px; font-weight:600; color:#dc2626; margin-bottom:12px;">⚠️ Outstanding Reimbursables</div>
"""
            for r in reimb_outstanding_items:
                category_icon = {'trip': '✈️', 'shipping': '📦', 'materials': '🎨', 'presentation': '📊', 'other': '📝'}.get(r['category'], '📝')
                html += f"""
                <div style="background:white; padding:15px; border-radius:8px; margin-bottom:8px; border-left:3px solid #dc2626;">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <span style="font-weight:600; color:#1e293b;">{r['invoice_number']}</span>
                            <span style="color:#64748b; margin-left:8px;">{category_icon}</span>
                        </div>
                        <div style="font-weight:700; color:#dc2626;">${r['amount_invoiced']:,.2f}</div>
                    </div>
                    <div style="font-size:12px; color:#64748b; margin-top:4px;">{r['description'][:80]}{'...' if len(r['description']) > 80 else ''}</div>
                    <div style="font-size:11px; color:#94a3b8; margin-top:4px;">Issued: {r['invoice_date']}</div>
                </div>
"""
            html += "</div>"

        # Recent Paid Reimbursables (collapsed view)
        if reimb_paid_items[:5]:
            html += """
            <div>
                <div style="font-size:14px; font-weight:600; color:#16a34a; margin-bottom:12px;">✅ Recently Paid Reimbursables</div>
"""
            for r in reimb_paid_items[:5]:
                category_icon = {'trip': '✈️', 'shipping': '📦', 'materials': '🎨', 'presentation': '📊', 'other': '📝'}.get(r['category'], '📝')
                html += f"""
                <div style="background:white; padding:12px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #e2e8f0;">
                    <table cellpadding="0" cellspacing="0" style="width:100%;">
                        <tr>
                            <td style="width:100px;"><span style="font-weight:600; color:#1e293b;">{r['invoice_number']}</span></td>
                            <td style="color:#64748b; font-size:12px;">{r['description'][:50]}{'...' if len(r['description']) > 50 else ''}</td>
                            <td style="width:100px; text-align:right; font-weight:600; color:#16a34a;">${r['amount_paid']:,.2f}</td>
                        </tr>
                    </table>
                </div>
"""
            if len(reimb_paid_items) > 5:
                html += f'<div style="color:#64748b; font-size:12px; text-align:center;">+ {len(reimb_paid_items) - 5} more paid reimbursables</div>'
            html += "</div>"

        html += "</div>"

    # Grand Total Section (Design + Reimbursables)
    if reimbursables['items']:
        html += f"""
        <div style="padding:25px 50px; background:#1e293b;">
            <table cellpadding="0" cellspacing="0" style="width:100%;">
                <tr>
                    <td style="color:white; font-size:16px; font-weight:600;">GRAND TOTAL OUTSTANDING (Design Fees + Reimbursables)</td>
                    <td style="text-align:right; color:#fca5a5; font-size:28px; font-weight:800;">${grand_total_outstanding:,.2f}</td>
                </tr>
            </table>
        </div>
"""

    # Outstanding invoices section
    if outstanding:
        total_outstanding_amt = sum((inv['invoice_amount'] or 0) - (inv['payment_amount'] or 0) for inv in outstanding)
        html += f"""
        <div class="outstanding-section">
            <div class="outstanding-title">
                <span>&#9888;</span> Outstanding Invoices Requiring Action
            </div>
"""
        for inv in outstanding:
            amt = (inv['invoice_amount'] or 0) - (inv['payment_amount'] or 0)
            html += f"""
            <div class="outstanding-item">
                <div class="outstanding-details">
                    <div class="outstanding-invoice">{inv['invoice_number']}</div>
                    <div class="outstanding-scope">{(inv.get('scope') or 'N/A').replace('-', ' ').title()} / {inv.get('phase', 'N/A')} &nbsp;|&nbsp; Invoiced: {inv.get('invoice_date', 'N/A')[:10] if inv.get('invoice_date') else 'N/A'}</div>
                </div>
                <div class="outstanding-amount">${amt:,.2f}</div>
            </div>
"""
        html += f"""
            <div class="outstanding-total">
                <div class="outstanding-total-label">TOTAL OUTSTANDING</div>
                <div class="outstanding-total-value">${total_outstanding_amt:,.2f}</div>
            </div>
        </div>
"""

    # Footer
    html += f"""
        <div class="footer">
            Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} &nbsp;|&nbsp; Bensley Design Studios
        </div>
    </div>
</body>
</html>
"""

    return html


def send_email(to_email: str, subject: str, html_content: str):
    """Send email via SMTP SSL"""
    # Get SMTP settings from environment (use EMAIL_ vars with SMTP defaults)
    smtp_server = os.getenv('EMAIL_SERVER', 'tmail.bensley.com')
    smtp_port = 465  # SSL port
    smtp_user = os.getenv('EMAIL_USERNAME', 'lukas@bensley.com')
    smtp_password = os.getenv('EMAIL_PASSWORD')
    from_email = smtp_user

    if not smtp_password:
        # Save to file instead
        filename = f"project_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, 'w') as f:
            f.write(html_content)
        print(f"SMTP not configured. Saved report to: {filename}")
        return filename

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email

    # Handle multiple recipients
    if isinstance(to_email, list):
        msg['To'] = ', '.join(to_email)
        recipients = to_email
    else:
        msg['To'] = to_email
        recipients = [to_email]

    msg.attach(MIMEText(html_content, 'html'))

    # Use SMTP_SSL for port 465
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, recipients, msg.as_string())

    print(f"Email sent to {to_email}")
    return True


if __name__ == '__main__':
    import sys

    project_name = sys.argv[1] if len(sys.argv) > 1 else "wynn marjan"
    to_email = sys.argv[2] if len(sys.argv) > 2 else "lukas@bensley.com"

    print(f"Generating report for: {project_name}")

    data = get_project_data(project_name)
    html = generate_html_email(data)

    # Save HTML file
    project_code = data['project']['project_code'].replace(' ', '_')
    filename = f"exports/project_report_{project_code}_{datetime.now().strftime('%Y%m%d')}.html"
    os.makedirs('exports', exist_ok=True)
    with open(filename, 'w') as f:
        f.write(html)

    print(f"Report saved to: {filename}")

    # Send email
    if to_email:
        subject = f"Project Status Report: {data['project']['project_title']} ({data['project']['project_code']})"
        send_email(to_email, subject, html)
    else:
        print(f"Open in browser: file://{os.path.abspath(filename)}")

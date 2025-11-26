#!/usr/bin/env python3
"""
Comprehensive Project Query Tool
Access EVERY piece of information about a project from all data sources

Once historical data is imported, this provides:
- Contract details & phases
- All invoices & payments
- Email communications
- PDF documents
- Project timeline
- Financial summary
- Health metrics
"""

import sqlite3
from datetime import datetime
import json

DB_PATH = "database/bensley_master.db"

def query_project_complete(project_code):
    """
    Get complete project information from all sources
    Returns comprehensive JSON with everything about the project
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    result = {
        'project_code': project_code,
        'query_timestamp': datetime.now().isoformat(),
        'data_sources': []
    }

    # =================================================================
    # 1. BASIC PROJECT INFO
    # =================================================================
    cursor.execute("""
        SELECT
            project_id,
            project_code,
            project_title,
            project_type,
            status,
            project_stage,
            total_fee_usd,
            date_created,
            first_contact_date,
            drafting_date,
            proposal_sent_date,
            contract_signed_date,
            notes
        FROM projects
        WHERE project_code = ?
    """, (project_code,))

    project = cursor.fetchone()
    if not project:
        conn.close()
        return {'error': f'Project {project_code} not found'}

    project_id = project[0]
    result['project'] = {
        'id': project[0],
        'code': project[1],
        'title': project[2],
        'type': project[3],
        'status': project[4],
        'stage': project[5],
        'total_fee_usd': project[6],
        'date_created': project[7],
        'first_contact_date': project[8],
        'drafting_date': project[9],
        'proposal_sent_date': project[10],
        'contract_signed_date': project[11],
        'notes': project[12]
    }
    result['data_sources'].append('projects')

    # =================================================================
    # 2. CONTRACT METADATA
    # =================================================================
    cursor.execute("""
        SELECT
            contract_date,
            contract_term_months,
            total_contract_value_usd,
            total_landscape_fee_usd,
            total_architecture_fee_usd,
            total_interior_fee_usd,
            total_branding_fee_usd,
            payment_due_days,
            late_payment_interest_rate,
            client_name,
            client_address
        FROM contract_metadata
        WHERE project_id = ?
    """, (project_id,))

    contract = cursor.fetchone()
    if contract:
        result['contract'] = {
            'date': contract[0],
            'term_months': contract[1],
            'total_value_usd': contract[2],
            'landscape_fee': contract[3],
            'architecture_fee': contract[4],
            'interior_fee': contract[5],
            'branding_fee': contract[6],
            'payment_due_days': contract[7],
            'late_interest_rate': contract[8],
            'client_name': contract[9],
            'client_address': contract[10]
        }
        result['data_sources'].append('contract_metadata')

    # =================================================================
    # 3. CONTRACT PHASES
    # =================================================================
    cursor.execute("""
        SELECT
            discipline,
            phase_name,
            phase_order,
            phase_fee_usd,
            invoiced_amount_usd,
            paid_amount_usd,
            status,
            start_date,
            actual_completion_date
        FROM contract_phases
        WHERE project_id = ?
        ORDER BY discipline, phase_order
    """, (project_id,))

    phases = []
    for row in cursor.fetchall():
        phases.append({
            'discipline': row[0],
            'phase': row[1],
            'order': row[2],
            'fee': row[3],
            'invoiced': row[4],
            'paid': row[5],
            'status': row[6],
            'start_date': row[7],
            'completion_date': row[8]
        })

    if phases:
        result['contract_phases'] = phases
        result['data_sources'].append('contract_phases')

    # =================================================================
    # 4. ALL INVOICES
    # =================================================================
    cursor.execute("""
        SELECT
            invoice_number,
            description,
            invoice_date,
            due_date,
            invoice_amount,
            payment_amount,
            payment_date,
            status,
            notes
        FROM invoices
        WHERE project_id = ?
        ORDER BY invoice_date DESC
    """, (project_id,))

    invoices = []
    for row in cursor.fetchall():
        invoices.append({
            'invoice_number': row[0],
            'description': row[1],
            'invoice_date': row[2],
            'due_date': row[3],
            'invoice_amount': row[4],
            'payment_amount': row[5],
            'payment_date': row[6],
            'status': row[7],
            'notes': row[8]
        })

    if invoices:
        result['invoices'] = invoices
        result['data_sources'].append('invoices')

    # =================================================================
    # 5. FINANCIAL SUMMARY
    # =================================================================
    cursor.execute("""
        SELECT
            COUNT(*) as invoice_count,
            SUM(invoice_amount) as total_invoiced,
            SUM(payment_amount) as total_paid,
            SUM(invoice_amount - payment_amount) as outstanding
        FROM invoices
        WHERE project_id = ?
    """, (project_id,))

    financial = cursor.fetchone()
    result['financial_summary'] = {
        'contract_value': result['project']['total_fee_usd'],
        'total_invoiced': financial[1] or 0,
        'total_paid': financial[2] or 0,
        'outstanding': financial[3] or 0,
        'invoice_count': financial[0],
        'invoiced_percentage': round((financial[1] or 0) / result['project']['total_fee_usd'] * 100, 1) if result['project']['total_fee_usd'] else 0,
        'paid_percentage': round((financial[2] or 0) / result['project']['total_fee_usd'] * 100, 1) if result['project']['total_fee_usd'] else 0
    }

    # =================================================================
    # 6. EMAILS (if email system is fully imported)
    # =================================================================
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master
        WHERE type='table' AND name='emails'
    """)

    if cursor.fetchone()[0] > 0:
        cursor.execute("""
            SELECT
                subject,
                sender_name,
                date,
                body_preview
            FROM emails
            WHERE subject LIKE ?
            ORDER BY date DESC
            LIMIT 50
        """, (f'%{project_code}%',))

        emails = []
        for row in cursor.fetchall():
            emails.append({
                'subject': row[0],
                'sender': row[1],
                'date': row[2],
                'preview': row[3]
            })

        if emails:
            result['emails'] = emails
            result['data_sources'].append('emails')

    # =================================================================
    # 7. PDF DOCUMENTS (if document system exists)
    # =================================================================
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master
        WHERE type='table' AND name='pdf_documents'
    """)

    if cursor.fetchone()[0] > 0:
        cursor.execute("""
            SELECT
                file_name,
                file_path,
                document_type,
                page_count,
                indexed_at
            FROM pdf_documents
            WHERE project_code = ?
            ORDER BY indexed_at DESC
        """, (project_code,))

        documents = []
        for row in cursor.fetchall():
            documents.append({
                'filename': row[0],
                'path': row[1],
                'type': row[2],
                'pages': row[3],
                'indexed': row[4]
            })

        if documents:
            result['documents'] = documents
            result['data_sources'].append('pdf_documents')

    # =================================================================
    # 8. PROJECT TIMELINE
    # =================================================================
    timeline = []

    if result['project']['first_contact_date']:
        timeline.append({
            'date': result['project']['first_contact_date'],
            'event': 'First Contact',
            'type': 'milestone'
        })

    if result['project']['drafting_date']:
        timeline.append({
            'date': result['project']['drafting_date'],
            'event': 'Drafting Started',
            'type': 'milestone'
        })

    if result['project']['proposal_sent_date']:
        timeline.append({
            'date': result['project']['proposal_sent_date'],
            'event': 'Proposal Sent',
            'type': 'milestone'
        })

    if result['project']['contract_signed_date']:
        timeline.append({
            'date': result['project']['contract_signed_date'],
            'event': 'Contract Signed',
            'type': 'milestone'
        })

    # Add invoice dates
    for inv in invoices:
        if inv['invoice_date']:
            timeline.append({
                'date': inv['invoice_date'],
                'event': f"Invoice {inv['invoice_number']} issued (${inv['invoice_amount']:,.0f})",
                'type': 'invoice'
            })
        if inv['payment_date']:
            timeline.append({
                'date': inv['payment_date'],
                'event': f"Payment received for {inv['invoice_number']} (${inv['payment_amount']:,.0f})",
                'type': 'payment'
            })

    # Sort timeline by date
    timeline.sort(key=lambda x: x['date'] if x['date'] else '9999-99-99')
    result['timeline'] = timeline

    # =================================================================
    # 9. PROJECT HEALTH METRICS
    # =================================================================
    result['health_metrics'] = {
        'is_active': result['project']['status'] == 'Active',
        'has_contract': 'contract' in result,
        'invoicing_complete': result['financial_summary']['invoiced_percentage'] >= 100,
        'payment_complete': result['financial_summary']['paid_percentage'] >= 100,
        'has_outstanding': result['financial_summary']['outstanding'] > 0,
        'data_completeness': len(result['data_sources']) / 7 * 100  # out of 7 possible sources
    }

    conn.close()
    return result


def print_project_summary(project_code):
    """Print human-readable project summary"""
    data = query_project_complete(project_code)

    if 'error' in data:
        print(f"❌ {data['error']}")
        return

    print("\n" + "=" * 100)
    print(f"COMPLETE PROJECT INFORMATION: {data['project']['code']}")
    print("=" * 100)

    # Project basics
    print(f"\n📋 PROJECT: {data['project']['title']}")
    print(f"   Status: {data['project']['status']} | Stage: {data['project']['stage']}")
    print(f"   Type: {data['project']['type']}")

    # Contract info
    if 'contract' in data:
        print(f"\n📄 CONTRACT:")
        print(f"   Date: {data['contract']['date']}")
        print(f"   Term: {data['contract']['term_months']} months")
        print(f"   Client: {data['contract']['client_name']}")
        print(f"   Total Value: ${data['contract']['total_value_usd']:,.2f}")
        if data['contract']['landscape_fee']:
            print(f"     - Landscape: ${data['contract']['landscape_fee']:,.2f}")
        if data['contract']['architecture_fee']:
            print(f"     - Architecture: ${data['contract']['architecture_fee']:,.2f}")
        if data['contract']['interior_fee']:
            print(f"     - Interior: ${data['contract']['interior_fee']:,.2f}")

    # Financial summary
    print(f"\n💰 FINANCIALS:")
    print(f"   Contract Value: ${data['financial_summary']['contract_value']:,.2f}")
    print(f"   Total Invoiced: ${data['financial_summary']['total_invoiced']:,.2f} ({data['financial_summary']['invoiced_percentage']}%)")
    print(f"   Total Paid: ${data['financial_summary']['total_paid']:,.2f} ({data['financial_summary']['paid_percentage']}%)")
    print(f"   Outstanding: ${data['financial_summary']['outstanding']:,.2f}")
    print(f"   Invoice Count: {data['financial_summary']['invoice_count']}")

    # Phases
    if 'contract_phases' in data:
        print(f"\n📊 CONTRACT PHASES: {len(data['contract_phases'])} phases")
        for phase in data['contract_phases'][:5]:  # Show first 5
            print(f"   {phase['discipline']:20} | {phase['phase']:25} | ${phase['fee']:,.0f} | {phase['status']}")
        if len(data['contract_phases']) > 5:
            print(f"   ... and {len(data['contract_phases']) - 5} more phases")

    # Recent invoices
    if 'invoices' in data:
        print(f"\n🧾 RECENT INVOICES:")
        for inv in data['invoices'][:5]:  # Show 5 most recent
            status_icon = "✅" if inv['status'] == 'paid' else "⏳" if inv['status'] == 'partial' else "📋"
            print(f"   {status_icon} {inv['invoice_number']:15} | {inv['invoice_date']} | ${inv['invoice_amount']:>10,.0f} | {inv['status']}")

    # Timeline highlights
    if data['timeline']:
        print(f"\n📅 KEY DATES:")
        milestone_events = [t for t in data['timeline'] if t['type'] == 'milestone']
        for event in milestone_events[:8]:
            print(f"   {event['date']} - {event['event']}")

    # Communications
    if 'emails' in data:
        print(f"\n📧 EMAIL COMMUNICATIONS: {len(data['emails'])} emails")
        for email in data['emails'][:3]:
            print(f"   {email['date']} | {email['sender']:30} | {email['subject'][:50]}")

    # Documents
    if 'documents' in data:
        print(f"\n📁 DOCUMENTS: {len(data['documents'])} files")
        for doc in data['documents'][:5]:
            print(f"   {doc['type']:15} | {doc['filename']}")

    # Health
    print(f"\n🏥 HEALTH METRICS:")
    print(f"   Active: {'✅' if data['health_metrics']['is_active'] else '❌'}")
    print(f"   Has Contract: {'✅' if data['health_metrics']['has_contract'] else '❌'}")
    print(f"   Invoicing Complete: {'✅' if data['health_metrics']['invoicing_complete'] else '⏳'}")
    print(f"   Payment Complete: {'✅' if data['health_metrics']['payment_complete'] else '⏳'}")
    print(f"   Data Completeness: {data['health_metrics']['data_completeness']:.0f}%")

    print(f"\n📊 DATA SOURCES: {', '.join(data['data_sources'])}")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 query_project_complete.py <project_code>")
        print("\nExamples:")
        print("  python3 query_project_complete.py '25 BK-043'")
        print("  python3 query_project_complete.py '22 BK-095'")
        sys.exit(1)

    project_code = sys.argv[1]

    # Option 1: Print summary
    print_project_summary(project_code)

    # Option 2: Get raw JSON (uncomment to use)
    # data = query_project_complete(project_code)
    # print(json.dumps(data, indent=2))

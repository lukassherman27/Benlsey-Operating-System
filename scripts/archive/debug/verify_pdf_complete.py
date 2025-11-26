#!/usr/bin/env python3
"""
COMPLETE PDF vs Database Verification Script
Extracts EVERY project entry from all 11 pages - including sub-projects
"""

import sqlite3
from decimal import Decimal

# Complete PDF extraction - ALL projects from all 11 pages
# Based on the PDF footer showing $66,520,603.00 total

PDF_PROJECTS = []

# PROJECT 1: 20 BK-047 - Audley Square House
PDF_PROJECTS.append({
    "project_code": "20 BK-047",
    "title": "Audley Square House-Communal Spa",
    "total_fee": 148000.00,
    "outstanding": 8000.00,
    "remaining": 116000.00,
    "paid": 24000.00
})

# PROJECT 2: 19 BK-018 - Villa Project in Ahmedabad (3 disciplines combined)
PDF_PROJECTS.append({
    "project_code": "19 BK-018",
    "title": "Villa Project in Ahmedabad, India",
    "total_fee": 1900000.00,  # 475k + 665k + 760k
    "outstanding": 151500.00,
    "remaining": 0.00,
    "paid": 1748000.00
})

# PROJECT 3: 22 BK-013 - Tel Aviv (Phase 1 + Monthly fees)
PDF_PROJECTS.append({
    "project_code": "22 BK-013",
    "title": "Tel Aviv High Rise Project in Israel",
    "total_fee": 4155000.00,  # LA Phase 1: 400k + ID Phase 1: 2,600k + Monthly: 1,155k
    "outstanding": 231000.00,
    "remaining": 2067000.00,
    "paid": 1857000.00
})

# PROJECT 4: 22 BK-046 - Nusa Penida (3 disciplines)
PDF_PROJECTS.append({
    "project_code": "22 BK-046",
    "title": "Resort and Hotel Project at Nusa Penida Island, Indonesia",
    "total_fee": 1700000.00,
    "outstanding": 255000.00,
    "remaining": 765000.00,
    "paid": 680000.00
})

# PROJECT 7: 22 BK-095 - Wynn Al Marjan (Multiple restaurants + additional)
PDF_PROJECTS.append({
    "project_code": "22 BK-095",
    "title": "Wynn Al Marjan Island Project",
    "total_fee": 3775000.00,  # 831,250 + 831,250 + 1,662,500 + 450,000 (excluding 25 BK-039)
    "outstanding": 202978.75,
    "remaining": 516148.75,
    "paid": 3224622.50
})

# PROJECT 7b: 25 BK-039 - Wynn Additional Service
PDF_PROJECTS.append({
    "project_code": "25 BK-039",
    "title": "Wynn Al Marjan Island Project - Additional Service Design Fee",
    "total_fee": 250000.00,
    "outstanding": 0.00,
    "remaining": 250000.00,
    "paid": 0.00
})

# PROJECT 8: 23 BK-009 - Le Parqe
PDF_PROJECTS.append({
    "project_code": "23 BK-009",
    "title": "Villa Project in Ahmedabad, India (Le Parqe Sector 5 and 7)",
    "total_fee": 730000.00,
    "outstanding": 219000.00,
    "remaining": 0.00,
    "paid": 511000.00
})

# PROJECT 9: 23 BK-028 - Proscenium (includes mural)
PDF_PROJECTS.append({
    "project_code": "23 BK-028",
    "title": "Proscenium Penthouse in Manila, Philippines",
    "total_fee": 1797520.00,
    "outstanding": 0.00,
    "remaining": 168000.00,
    "paid": 1629520.00
})

# PROJECT 10: 23 BK-088 - Mandarin Oriental Bali
PDF_PROJECTS.append({
    "project_code": "23 BK-088",
    "title": "Mandarin Oriental Bali Hotel and Branded Residential, Indonesia",
    "total_fee": 575000.00,
    "outstanding": 43125.00,
    "remaining": 129375.00,
    "paid": 402500.00
})

# PROJECT 10b: 25 BK-030 - Beach Club at Mandarin Oriental Bali
PDF_PROJECTS.append({
    "project_code": "25 BK-030",
    "title": "Beach Club at Mandarin Oriental Bali",
    "total_fee": 550000.00,
    "outstanding": 137500.00,
    "remaining": 330000.00,
    "paid": 82500.00
})

# PROJECT 11: 25 BK-018 - Ritz Carlton Nanyan Bay extension
PDF_PROJECTS.append({
    "project_code": "25 BK-018",
    "title": "The Ritz Carlton Hotel Nanyan Bay, China (One year Extension)",
    "total_fee": 225000.00,
    "outstanding": 56250.00,
    "remaining": 56250.00,
    "paid": 112500.00
})

# PROJECT 12: 23 BK-071 - St. Regis Thousand Island Interior
PDF_PROJECTS.append({
    "project_code": "23 BK-071",
    "title": "St. Regis Hotel in Thousand Island Lake, China - Interior Design",
    "total_fee": 1350000.00,
    "outstanding": 101250.00,
    "remaining": 708750.00,
    "paid": 540000.00
})

# PROJECT 12b: 23 BK-096 - St. Regis Thousand Island Addendum
PDF_PROJECTS.append({
    "project_code": "23 BK-096",
    "title": "St. Regis Hotel in Thousand Island Lake, China (Addendum)",
    "total_fee": 500000.00,
    "outstanding": 75000.00,
    "remaining": 112500.00,
    "paid": 312500.00
})

# PROJECT 13: 23 BK-067 - Treasure Island Interior
PDF_PROJECTS.append({
    "project_code": "23 BK-067",
    "title": "Treasure Island Resort, Intercontinental Hotel, Anji - Interior",
    "total_fee": 1200000.00,
    "outstanding": 0.00,
    "remaining": 648000.00,
    "paid": 552000.00
})

# PROJECT 13b: 23 BK-080 - Treasure Island Landscape
PDF_PROJECTS.append({
    "project_code": "23 BK-080",
    "title": "Treasure Island Resort, Intercontinental Hotel, Anji - Landscape",
    "total_fee": 400000.00,
    "outstanding": 0.00,
    "remaining": 216000.00,
    "paid": 184000.00
})

# PROJECT 14: 23 BK-093 - Mumbai (all 3 components)
PDF_PROJECTS.append({
    "project_code": "23 BK-093",
    "title": "25 Downtown Mumbai, India (Art Deco Residential)",
    "total_fee": 3250000.00,  # LA: 1M + ID: 1.5M + Redesign: 750k
    "outstanding": 262500.00,
    "remaining": 600000.00,
    "paid": 2387500.00
})

# PROJECT 15: 23 BK-089 - Jyoti's farm house
PDF_PROJECTS.append({
    "project_code": "23 BK-089",
    "title": "Jyoti's farm house in Delhi, India",
    "total_fee": 1000000.00,
    "outstanding": 0.00,
    "remaining": 225000.00,
    "paid": 775000.00
})

# PROJECT 16: 23 BK-050 - Bodrum Turkey (includes additional payments)
PDF_PROJECTS.append({
    "project_code": "23 BK-050",
    "title": "Ultra Luxury Beach Resort Hotel and Residence, Bodrum, Turkey",
    "total_fee": 4650000.00,
    "outstanding": 0.00,
    "remaining": 2561359.38,
    "paid": 2088640.63
})

# PROJECT 17: 24 BK-021 - Capella Ubud
PDF_PROJECTS.append({
    "project_code": "24 BK-021",
    "title": "Capella Hotel and Resort, Ubud Bali",
    "total_fee": 345000.00,
    "outstanding": 43125.00,
    "remaining": 207000.00,
    "paid": 94875.00
})

# PROJECT 18: 24 BK-018 - Luang Prabang (3 disciplines)
PDF_PROJECTS.append({
    "project_code": "24 BK-018",
    "title": "Luang Prabang Heritage Arcade and Hotel, Laos",
    "total_fee": 1450000.00,
    "outstanding": 0.00,
    "remaining": 870000.00,
    "paid": 580000.00
})

# PROJECT 19: 24 BK-029 - Qinhu Resort (3 disciplines)
PDF_PROJECTS.append({
    "project_code": "24 BK-029",
    "title": "Qinhu Resort Project, China",
    "total_fee": 3250000.00,
    "outstanding": 650000.00,
    "remaining": 2356250.00,
    "paid": 243750.00
})

# PROJECT 20: 19 BK-052 - The Siam Hotel Chiangmai (3 disciplines)
PDF_PROJECTS.append({
    "project_code": "19 BK-052",
    "title": "The Siam Hotel Chiangmai",
    "total_fee": 814500.00,
    "outstanding": 0.00,
    "remaining": 445800.00,
    "paid": 368700.00
})

# PROJECT 21: 24 BK-033 - Four Seasons monthly fees
PDF_PROJECTS.append({
    "project_code": "24 BK-033",
    "title": "Renovation Work for Three of Four Seasons Properties",
    "total_fee": 1500000.00,
    "outstanding": 34375.00,
    "remaining": 1031250.00,
    "paid": 434375.00
})

# PROJECT 22: 24 BK-077 - Raffles Singapore
PDF_PROJECTS.append({
    "project_code": "24 BK-077",
    "title": "Restaurant at the Raffles Hotel, Singapore",
    "total_fee": 195000.00,
    "outstanding": 0.00,
    "remaining": 29250.00,
    "paid": 165750.00
})

# PROJECT 23: 24 BK-058 - Fenfushi Maldives (3 disciplines)
PDF_PROJECTS.append({
    "project_code": "24 BK-058",
    "title": "Luxury Resort Development at Fenfushi Island, Raa Atoll, Maldives",
    "total_fee": 2990000.00,
    "outstanding": 526000.00,
    "remaining": 448500.00,
    "paid": 2015500.00
})

# PROJECT 24: 24 BK-074 - Hanoi Vietnam (3 disciplines)
PDF_PROJECTS.append({
    "project_code": "24 BK-074",
    "title": "43 Dang Thai Mai Project, Hanoi, Vietnam",
    "total_fee": 4900000.00,
    "outstanding": 1001725.00,
    "remaining": 808500.00,
    "paid": 3089775.00
})

# PROJECT 25: 25 BK-015 - Shinta Mani Mustang (2 hotels)
PDF_PROJECTS.append({
    "project_code": "25 BK-015",
    "title": "Shinta Mani Mustang, Nepal (Extension Work)",
    "total_fee": 300000.00,
    "outstanding": 120000.00,
    "remaining": 135000.00,
    "paid": 45000.00
})

# PROJECT 26: 25 BK-017 - TARC Delhi (LA + ID)
PDF_PROJECTS.append({
    "project_code": "25 BK-017",
    "title": "TARC's Luxury Branded Residence Project in New Delhi",
    "total_fee": 3000000.00,
    "outstanding": 131250.00,
    "remaining": 2418750.00,
    "paid": 450000.00
})

# PROJECT 27: 25 BK-033 - Ritz Carlton Nusa Dua (3 disciplines)
PDF_PROJECTS.append({
    "project_code": "25 BK-033",
    "title": "The Ritz Carlton Reserve, Nusa Dua, Bali, Indonesia",
    "total_fee": 3150000.00,
    "outstanding": 393750.00,
    "remaining": 1890000.00,
    "paid": 1023750.00
})

# PROJECT 27b: 25 BK-040 - Ritz Carlton Branding
PDF_PROJECTS.append({
    "project_code": "25 BK-040",
    "title": "The Ritz Carlton Reserve, Nusa Dua, Bali - Branding Consultancy",
    "total_fee": 125000.00,
    "outstanding": 0.00,
    "remaining": 93750.00,
    "paid": 31250.00
})

def connect_db():
    """Connect to the database"""
    db_path = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
    return sqlite3.connect(db_path)

def get_database_projects():
    """Get all projects from the database"""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT project_code, project_title, total_fee_usd
        FROM projects
        ORDER BY project_code
    """)

    projects = {}
    for row in cursor.fetchall():
        project_code, title, total_fee = row
        projects[project_code] = {
            "title": title,
            "total_fee": float(total_fee) if total_fee else 0.00
        }

    conn.close()
    return projects

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"

def main():
    db_projects = get_database_projects()

    print("=" * 160)
    print(" " * 50 + "COMPREHENSIVE PDF vs DATABASE VERIFICATION REPORT")
    print("=" * 160)
    print()

    # Calculate PDF totals
    pdf_total = sum(p["total_fee"] for p in PDF_PROJECTS)
    pdf_outstanding = sum(p["outstanding"] for p in PDF_PROJECTS)
    pdf_remaining = sum(p["remaining"] for p in PDF_PROJECTS)
    pdf_paid = sum(p["paid"] for p in PDF_PROJECTS)

    # Calculate DB total for matching projects
    db_total_matching = sum(db_projects[p["project_code"]]["total_fee"]
                           for p in PDF_PROJECTS
                           if p["project_code"] in db_projects)

    print(f"SUMMARY")
    print(f"-" * 160)
    print(f"Projects extracted from PDF:          {len(PDF_PROJECTS)}")
    print(f"PDF Grand Total (from footer):        {format_currency(66520603.00)}")
    print(f"PDF Calculated Total (my extraction): {format_currency(pdf_total)}")
    print(f"Difference:                           {format_currency(66520603.00 - pdf_total)}")
    print()
    print(f"Outstanding Total:  {format_currency(pdf_outstanding)} (Footer: {format_currency(5903166.25)})")
    print(f"Remaining Total:    {format_currency(pdf_remaining)} (Footer: {format_currency(32803726.13)})")
    print(f"Paid Total:         {format_currency(pdf_paid)} (Footer: {format_currency(27971210.63)})")
    print()

    # Line by line comparison
    print("=" * 160)
    print(f"{'#':<4} {'Project Code':<12} {'Description':<55} {'PDF Total':<18} {'DB Total':<18} {'Status':<10} {'Difference':<18}")
    print("=" * 160)

    matches = []
    mismatches = []
    missing_from_db = []

    for idx, project in enumerate(PDF_PROJECTS, 1):
        code = project["project_code"]
        title = project["title"][:52] + "..." if len(project["title"]) > 55 else project["title"]
        pdf_fee = project["total_fee"]

        if code in db_projects:
            db_fee = db_projects[code]["total_fee"]
            diff = pdf_fee - db_fee

            if abs(diff) < 0.01:
                status = "MATCH ✓"
                matches.append(code)
            else:
                status = "MISMATCH ✗"
                mismatches.append({
                    "code": code,
                    "title": title,
                    "pdf_fee": pdf_fee,
                    "db_fee": db_fee,
                    "diff": diff
                })

            print(f"{idx:<4} {code:<12} {title:<55} {format_currency(pdf_fee):<18} {format_currency(db_fee):<18} {status:<10} {format_currency(diff):<18}")
        else:
            status = "MISSING ✗"
            missing_from_db.append({
                "code": code,
                "title": title,
                "pdf_fee": pdf_fee
            })
            print(f"{idx:<4} {code:<12} {title:<55} {format_currency(pdf_fee):<18} {'NOT IN DB':<18} {status:<10} {'N/A':<18}")

    print("=" * 160)
    print()

    # Detailed results
    print("=" * 160)
    print("DETAILED ANALYSIS")
    print("=" * 160)
    print()

    print(f"1. MATCHING PROJECTS: {len(matches)}")
    print(f"-" * 160)
    for code in matches:
        proj = next(p for p in PDF_PROJECTS if p["project_code"] == code)
        print(f"   ✓ {code}: {proj['title']}")
    print()

    print(f"2. MISMATCHED PROJECTS: {len(mismatches)}")
    print(f"-" * 160)
    for m in mismatches:
        print(f"   ✗ {m['code']}: {m['title']}")
        print(f"      PDF:  {format_currency(m['pdf_fee'])}")
        print(f"      DB:   {format_currency(m['db_fee'])}")
        print(f"      Diff: {format_currency(m['diff'])} {'(PDF > DB - need to UPDATE DB)' if m['diff'] > 0 else '(DB > PDF - need to CHECK PDF)'}")
        print()

    print(f"3. MISSING FROM DATABASE: {len(missing_from_db)}")
    print(f"-" * 160)
    for m in missing_from_db:
        print(f"   • {m['code']}: {m['title']}")
        print(f"      Fee: {format_currency(m['pdf_fee'])} - NEEDS TO BE ADDED TO DATABASE")
        print()

    # Grand totals check
    print("=" * 160)
    print("GRAND TOTALS VERIFICATION")
    print("=" * 160)
    print()

    print(f"{'Metric':<25} {'My Calculation':<20} {'PDF Footer':<20} {'Difference':<20} {'Status':<10}")
    print(f"-" * 160)

    total_diff = pdf_total - 66520603.00
    out_diff = pdf_outstanding - 5903166.25
    rem_diff = pdf_remaining - 32803726.13
    paid_diff = pdf_paid - 27971210.63

    print(f"{'Total Fee':<25} {format_currency(pdf_total):<20} {format_currency(66520603.00):<20} {format_currency(total_diff):<20} {'✓' if abs(total_diff) < 100 else '✗':<10}")
    print(f"{'Outstanding':<25} {format_currency(pdf_outstanding):<20} {format_currency(5903166.25):<20} {format_currency(out_diff):<20} {'✓' if abs(out_diff) < 100 else '✗':<10}")
    print(f"{'Remaining':<25} {format_currency(pdf_remaining):<20} {format_currency(32803726.13):<20} {format_currency(rem_diff):<20} {'✓' if abs(rem_diff) < 100 else '✗':<10}")
    print(f"{'Paid':<25} {format_currency(pdf_paid):<20} {format_currency(27971210.63):<20} {format_currency(paid_diff):<20} {'✓' if abs(paid_diff) < 100 else '✗':<10}")
    print()

    # Action items
    print("=" * 160)
    print("ACTION ITEMS")
    print("=" * 160)
    print()

    if len(mismatches) > 0:
        print(f"1. FIX {len(mismatches)} MISMATCHED PROJECTS in database:")
        for m in mismatches:
            if m['diff'] > 0:
                print(f"   UPDATE projects SET total_fee_usd = {m['pdf_fee']} WHERE project_code = '{m['code']}';")
    print()

    if len(missing_from_db) > 0:
        print(f"2. ADD {len(missing_from_db)} MISSING PROJECTS to database")
        print("   (These projects exist in PDF but not in database)")
    print()

    if abs(total_diff) > 100:
        print(f"3. INVESTIGATE TOTAL DIFFERENCE: {format_currency(total_diff)}")
        print(f"   My extraction may be missing some projects or combining incorrectly")
    print()

    return {
        "matches": len(matches),
        "mismatches": len(mismatches),
        "missing": len(missing_from_db),
        "total_diff": total_diff
    }

if __name__ == "__main__":
    results = main()

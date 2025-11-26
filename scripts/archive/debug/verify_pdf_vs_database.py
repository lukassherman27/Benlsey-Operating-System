#!/usr/bin/env python3
"""
Comprehensive PDF vs Database Verification Script
Extracts EVERY project entry from the PDF and compares line-by-line with the database
"""

import sqlite3
from decimal import Decimal
from collections import defaultdict
import re

# PDF Data Structure - Extracted from all 11 pages
# Format: project_code: {title, total_fee, outstanding, remaining, paid}

PDF_PROJECTS = {
    # Page 1
    "20 BK-047": {
        "title": "Audley Square House-Communal Spa",
        "total_fee": 148000.00,  # 40,000 (old installments) + 108,000 (new installments)
        "outstanding": 8000.00,
        "remaining": 116000.00,  # 8,000 + 108,000
        "paid": 24000.00,
        "disciplines": ["Monthly Installments"]
    },

    "19 BK-018": {
        "title": "Villa Project in Ahmedabad, India",
        "total_fee": 1900000.00,  # Landscape 475k + Architectural 665k + Interior 760k
        "outstanding": 151500.00,  # 35,625 + 49,875 + 66,500
        "remaining": 0.00,
        "paid": 1748000.00,  # 439,375 + 615,125 + 693,500
        "disciplines": ["Landscape Architectural", "Architectural", "Interior Design"],
        "breakdown": {
            "Landscape Architectural": {
                "total_fee": 475000.00,
                "outstanding": 35625.00,
                "remaining": 0.00,
                "paid": 439375.00
            },
            "Architectural": {
                "total_fee": 665000.00,
                "outstanding": 49875.00,
                "remaining": 0.00,
                "paid": 615125.00
            },
            "Interior Design": {
                "total_fee": 760000.00,
                "outstanding": 66500.00,
                "remaining": 0.00,
                "paid": 693500.00
            }
        }
    },

    # Page 2
    "22 BK-013": {
        "title": "Tel Aviv High Rise Project in Israel",
        "total_fee": 4155000.00,  # LA Phase 1: 400k + ID Phase 1: 2,600k + Monthly: 1,155k
        "outstanding": 231000.00,
        "remaining": 2067000.00,  # 240,000 + 1,365,000 + 462,000
        "paid": 1857000.00,  # 160,000 + 1,235,000 + 462,000
        "disciplines": ["Landscape Architectural-Phase 1", "Interior Design-Phase 1", "Design Development and Construction Documents"],
        "breakdown": {
            "Landscape Architectural-Phase 1": {
                "total_fee": 400000.00,
                "outstanding": 0.00,
                "remaining": 240000.00,
                "paid": 160000.00
            },
            "Interior Design-Phase 1": {
                "total_fee": 2600000.00,
                "outstanding": 0.00,
                "remaining": 1365000.00,
                "paid": 1235000.00
            },
            "Monthly Fee Charge for 10 months": {
                "total_fee": 1155000.00,
                "outstanding": 231000.00,
                "remaining": 462000.00,
                "paid": 462000.00
            }
        }
    },

    "22 BK-046": {
        "title": "Resort and Hotel Project at Nusa Penida Island, Indonesia",
        "total_fee": 1700000.00,  # LA: 450k + Arch: 600k + ID: 650k
        "outstanding": 255000.00,  # 67,500 + 90,000 + 97,500
        "remaining": 765000.00,  # 202,500 + 270,000 + 292,500
        "paid": 680000.00,  # 180,000 + 240,000 + 260,000
        "disciplines": ["Landscape Architectural", "Architectural", "Interior Design"],
        "breakdown": {
            "Landscape Architectural": {
                "total_fee": 450000.00,
                "outstanding": 67500.00,
                "remaining": 202500.00,
                "paid": 180000.00
            },
            "Architectural": {
                "total_fee": 600000.00,
                "outstanding": 90000.00,
                "remaining": 270000.00,
                "paid": 240000.00
            },
            "Interior Design": {
                "total_fee": 650000.00,
                "outstanding": 97500.00,
                "remaining": 292500.00,
                "paid": 260000.00
            }
        }
    },

    # Page 3
    "22 BK-095": {
        "title": "Wynn Al Marjan Island Project",
        "total_fee": 4193750.00,  # Indian Brasserie: 831,250 + Modern Med: 831,250 + Day Club: 1,662,500 + Night Club: 450,000 + Additional: 250,000 + Addendum: 168,750
        "outstanding": 202978.75,  # 0 + 31,172.50 + 77,306.25 + 47,250 + 0 + 47,250
        "remaining": 766148.75,  # 93,517.50 + 93,517.50 + 246,881.25 + 87,750 + 250,000 + 87,750
        "paid": 3224622.50,  # 737,732.50 + 706,560 + 1,338,312.50 + 315,000 + 0 + 315,000
        "disciplines": ["Indian Brasserie #473", "Modern Mediterranean #477", "Day Club #650", "Night Club", "Additional Service"],
        "breakdown": {
            "Indian Brasserie at Casino level #473": {
                "total_fee": 831250.00,
                "outstanding": 0.00,
                "remaining": 93517.50,
                "paid": 737732.50
            },
            "Modern Mediterranean Restaurant on Casino Level #477": {
                "total_fee": 831250.00,
                "outstanding": 31172.50,
                "remaining": 93517.50,
                "paid": 706560.00
            },
            "Day Club on B2 Level including Dynamic outdoor Bar/swim up Bar #650": {
                "total_fee": 1662500.00,
                "outstanding": 77306.25,
                "remaining": 246881.25,
                "paid": 1338312.50
            },
            "Interior Design for Night Club": {
                "total_fee": 450000.00,
                "outstanding": 47250.00,
                "remaining": 87750.00,
                "paid": 315000.00
            },
            "Additional Service Design Fee (25 BK-039)": {
                "total_fee": 250000.00,
                "outstanding": 0.00,
                "remaining": 250000.00,
                "paid": 0.00
            }
        }
    },

    "23 BK-009": {
        "title": "Villa Project in Ahmedabad, India (Le Parqe Sector 5 and 7)",
        "total_fee": 730000.00,
        "outstanding": 219000.00,  # 71,175 + 38,325 + 71,175 + 38,325
        "remaining": 0.00,
        "paid": 511000.00,
        "disciplines": ["Landscape Architectural"]
    },

    # Page 4
    "23 BK-028": {
        "title": "Proscenium Penthouse in Manila, Philippines",
        "total_fee": 1797520.00,  # Main project: 1,400,000 + Mural: 397,520
        "outstanding": 0.00,
        "remaining": 168000.00,
        "paid": 1629520.00,
        "disciplines": ["Interior Design", "Mural (60th Floor & 62nd Floor)"],
        "breakdown": {
            "Interior Design": {
                "total_fee": 1400000.00,
                "outstanding": 0.00,
                "remaining": 168000.00,
                "paid": 1232000.00
            },
            "Mural (60th Floor & 62nd Floor)": {
                "total_fee": 397520.00,
                "outstanding": 0.00,
                "remaining": 0.00,
                "paid": 397520.00
            }
        }
    },

    "23 BK-088": {
        "title": "Mandarin Oriental Bali Hotel and Branded Residential, Indonesia",
        "total_fee": 575000.00,
        "outstanding": 43125.00,
        "remaining": 129375.00,
        "paid": 402500.00,
        "disciplines": ["Interior Design"]
    },

    "25 BK-030": {
        "title": "Beach Club at Mandarin Oriental Bali",
        "total_fee": 550000.00,  # Architectural: 220k + Interior: 330k
        "outstanding": 137500.00,  # 55,000 + 82,500
        "remaining": 330000.00,  # 132,000 + 198,000
        "paid": 82500.00,  # 33,000 + 49,500
        "disciplines": ["Architectural", "Interior Design"],
        "breakdown": {
            "Architectural": {
                "total_fee": 220000.00,
                "outstanding": 55000.00,
                "remaining": 132000.00,
                "paid": 33000.00
            },
            "Interior Design": {
                "total_fee": 330000.00,
                "outstanding": 82500.00,
                "remaining": 198000.00,
                "paid": 49500.00
            }
        }
    },

    "25 BK-018": {
        "title": "The Ritz Carlton Hotel Nanyan Bay, China (One year Extension Contract Mar 25-Mar 26)",
        "total_fee": 225000.00,
        "outstanding": 56250.00,
        "remaining": 56250.00,
        "paid": 112500.00,
        "disciplines": ["Monthly Installments"]
    },

    "23 BK-071": {
        "title": "St. Regis Hotel in Thousand Island Lake, China",
        "total_fee": 1350000.00,
        "outstanding": 101250.00,
        "remaining": 708750.00,
        "paid": 540000.00,
        "disciplines": ["Interior Design"]
    },

    "23 BK-096": {
        "title": "St. Regis Hotel in Thousand Island Lake, China (Addendum of Agreement)",
        "total_fee": 500000.00,
        "outstanding": 75000.00,
        "remaining": 112500.00,
        "paid": 312500.00,
        "disciplines": ["Landscape Architect and Architectural Façade"]
    },

    # Page 5
    "23 BK-067": {
        "title": "Treasure Island Resort, Intercontinental Hotel, Anji, Zhejiang, China",
        "total_fee": 1200000.00,
        "outstanding": 0.00,
        "remaining": 648000.00,
        "paid": 552000.00,
        "disciplines": ["Interior Design"]
    },

    "23 BK-080": {
        "title": "Treasure Island Resort, Intercontinental Hotel, Anji, Zhejiang, China",
        "total_fee": 400000.00,
        "outstanding": 0.00,
        "remaining": 216000.00,
        "paid": 184000.00,
        "disciplines": ["Landscape Architect"]
    },

    "23 BK-093": {
        "title": "25 Downtown Mumbai, India (Art Deco Residential Project in Mumbai, India)",
        "total_fee": 3250000.00,  # LA: 1,000,000 + ID: 1,500,000 + Redesign: 750,000
        "outstanding": 262500.00,  # 105,000 + 157,500 + 0
        "remaining": 600000.00,  # 150,000 + 225,000 + 225,000
        "paid": 2387500.00,  # 745,000 + 1,117,500 + 525,000
        "disciplines": ["Landscape Architectural", "Interior Design", "Redesign of Design Development Drawing"],
        "breakdown": {
            "Landscape Architectural": {
                "total_fee": 1000000.00,
                "outstanding": 105000.00,
                "remaining": 150000.00,
                "paid": 745000.00
            },
            "Interior Design": {
                "total_fee": 1500000.00,
                "outstanding": 157500.00,
                "remaining": 225000.00,
                "paid": 1117500.00
            },
            "Redesign of Design Development Drawing": {
                "total_fee": 750000.00,
                "outstanding": 0.00,
                "remaining": 225000.00,
                "paid": 525000.00
            }
        }
    },

    # Page 6
    "23 BK-089": {
        "title": "Jyoti's farm house in Delhi, India",
        "total_fee": 1000000.00,
        "outstanding": 0.00,
        "remaining": 225000.00,
        "paid": 775000.00,
        "disciplines": ["Interior Design"]
    },

    "23 BK-050": {
        "title": "Ultra Luxury Beach Resort Hotel and Residence, Bodrum, Turkey",
        "total_fee": 4650000.00,  # Main: 4,370,000 + Additional: 280,000
        "outstanding": 0.00,
        "remaining": 2561359.38,
        "paid": 2088640.63,
        "disciplines": ["Landscape Architectural", "Architectural", "Interior Design", "Additional Payments"],
        "breakdown": {
            "Main Project": {
                "total_fee": 4370000.00,
                "outstanding": 0.00,
                "remaining": 2281359.38,
                "paid": 2088640.63
            },
            "Additional Payments": {
                "total_fee": 280000.00,
                "outstanding": 0.00,
                "remaining": 280000.00,
                "paid": 0.00
            }
        }
    },

    "24 BK-021": {
        "title": "Capella Hotel and Resort, Ubud Bali (Extension of Capella Ubud)",
        "total_fee": 345000.00,
        "outstanding": 43125.00,
        "remaining": 207000.00,
        "paid": 94875.00,
        "disciplines": ["Interior Design"]
    },

    # Page 7
    "24 BK-018": {
        "title": "Luang Prabang Heritage Arcade and Hotel, Laos- The Shinta Mani (4 star)",
        "total_fee": 1450000.00,  # LA: 360k + Arch: 510k + ID: 580k
        "outstanding": 0.00,
        "remaining": 870000.00,  # 216,000 + 306,000 + 348,000
        "paid": 580000.00,  # 144,000 + 204,000 + 232,000
        "disciplines": ["Landscape Architectural", "Architectural", "Interior Design"],
        "breakdown": {
            "Landscape Architectural": {
                "total_fee": 360000.00,
                "outstanding": 0.00,
                "remaining": 216000.00,
                "paid": 144000.00
            },
            "Architectural": {
                "total_fee": 510000.00,
                "outstanding": 0.00,
                "remaining": 306000.00,
                "paid": 204000.00
            },
            "Interior Design": {
                "total_fee": 580000.00,
                "outstanding": 0.00,
                "remaining": 348000.00,
                "paid": 232000.00
            }
        }
    },

    "24 BK-029": {
        "title": "Qinhu Resort Project, China",
        "total_fee": 3250000.00,  # LA: 800k + Arch: 1,150k + ID: 1,300k
        "outstanding": 650000.00,  # 160,000 + 230,000 + 260,000
        "remaining": 2356250.00,  # 580,000 + 833,750 + 942,500
        "paid": 243750.00,  # 60,000 + 86,250 + 97,500
        "disciplines": ["Landscape Architectural", "Architectural", "Interior Design"],
        "breakdown": {
            "Landscape Architectural": {
                "total_fee": 800000.00,
                "outstanding": 160000.00,
                "remaining": 580000.00,
                "paid": 60000.00
            },
            "Architectural": {
                "total_fee": 1150000.00,
                "outstanding": 230000.00,
                "remaining": 833750.00,
                "paid": 86250.00
            },
            "Interior Design": {
                "total_fee": 1300000.00,
                "outstanding": 260000.00,
                "remaining": 942500.00,
                "paid": 97500.00
            }
        }
    },

    # Page 8
    "19 BK-052": {
        "title": "The Siam Hotel Chiangmai",
        "total_fee": 814500.00,  # LA: 200k + Arch: 286k + ID: 328.5k
        "outstanding": 0.00,
        "remaining": 445800.00,  # 120,000 + 128,700 + 197,100
        "paid": 368700.00,  # 80,000 + 157,300 + 131,400
        "disciplines": ["Landscape Architectural", "Architectural", "Interior Design"],
        "breakdown": {
            "Landscape Architectural": {
                "total_fee": 200000.00,
                "outstanding": 0.00,
                "remaining": 120000.00,
                "paid": 80000.00
            },
            "Architectural": {
                "total_fee": 286000.00,
                "outstanding": 0.00,
                "remaining": 128700.00,
                "paid": 157300.00
            },
            "Interior Design": {
                "total_fee": 328500.00,
                "outstanding": 0.00,
                "remaining": 197100.00,
                "paid": 131400.00
            }
        }
    },

    "24 BK-033": {
        "title": "Renovation Work for Three of Four Seasons Properties",
        "total_fee": 1500000.00,
        "outstanding": 34375.00,
        "remaining": 1031250.00,
        "paid": 434375.00,
        "disciplines": ["Monthly Fee"]
    },

    # Page 9
    "24 BK-077": {
        "title": "Restaurant at the Raffles Hotel, Singapore",
        "total_fee": 195000.00,
        "outstanding": 0.00,
        "remaining": 29250.00,
        "paid": 165750.00,
        "disciplines": ["Interior Design"]
    },

    "24 BK-058": {
        "title": "Luxury Resort Development at Fenfushi Island, Raa Atoll, Maldives",
        "total_fee": 2990000.00,  # LA: 480k + Arch: 1,010k + ID: 1,500k
        "outstanding": 526000.00,  # 84,441 + 177,679 + 263,880
        "remaining": 448500.00,  # 72,000 + 151,500 + 225,000
        "paid": 2015500.00,  # 323,559 + 680,821 + 1,011,120
        "disciplines": ["Landscape Architectural", "Architectural", "Interior Design"],
        "breakdown": {
            "Landscape Architectural": {
                "total_fee": 480000.00,
                "outstanding": 84441.00,
                "remaining": 72000.00,
                "paid": 323559.00
            },
            "Architectural": {
                "total_fee": 1010000.00,
                "outstanding": 177679.00,
                "remaining": 151500.00,
                "paid": 680821.00
            },
            "Interior Design": {
                "total_fee": 1500000.00,
                "outstanding": 263880.00,
                "remaining": 225000.00,
                "paid": 1011120.00
            }
        }
    },

    "24 BK-074": {
        "title": "43 Dang Thai Mai Project, Hanoi, Vietnam",
        "total_fee": 4900000.00,  # LA: 1,225k + Arch: 1,715k + ID: 1,960k
        "outstanding": 1001725.00,  # 349,125 + 0 + 652,600
        "remaining": 808500.00,  # 202,125 + 282,975 + 323,400
        "paid": 3089775.00,  # 673,750 + 1,432,025 + 984,000
        "disciplines": ["Landscape Architectural", "Architectural", "Interior Design"],
        "breakdown": {
            "Landscape Architectural": {
                "total_fee": 1225000.00,
                "outstanding": 349125.00,
                "remaining": 202125.00,
                "paid": 673750.00
            },
            "Architectural": {
                "total_fee": 1715000.00,
                "outstanding": 0.00,
                "remaining": 282975.00,
                "paid": 1432025.00
            },
            "Interior Design": {
                "total_fee": 1960000.00,
                "outstanding": 652600.00,
                "remaining": 323400.00,
                "paid": 984000.00
            }
        }
    },

    # Page 10
    "25 BK-015": {
        "title": "Shinta Mani Mustang, Nepal (Extension Work)-Hotel #1 and #2",
        "total_fee": 300000.00,  # Hotel #1: 150k + Hotel #2: 150k
        "outstanding": 120000.00,  # 60,000 + 60,000
        "remaining": 135000.00,  # 67,500 + 67,500
        "paid": 45000.00,  # 22,500 + 22,500
        "disciplines": ["Interior Design"],
        "breakdown": {
            "Hotel #1": {
                "total_fee": 150000.00,
                "outstanding": 60000.00,
                "remaining": 67500.00,
                "paid": 22500.00
            },
            "Hotel #2": {
                "total_fee": 150000.00,
                "outstanding": 60000.00,
                "remaining": 67500.00,
                "paid": 22500.00
            }
        }
    },

    "25 BK-017": {
        "title": "TARC's Luxury Branded Residence Project in New Delhi",
        "total_fee": 3000000.00,  # LA: 1,050k + ID: 1,950k
        "outstanding": 131250.00,
        "remaining": 2418750.00,  # 761,250 + 1,657,500
        "paid": 450000.00,  # 157,500 + 292,500
        "disciplines": ["Landscape Architectural", "Interior Design"],
        "breakdown": {
            "Landscape Architectural": {
                "total_fee": 1050000.00,
                "outstanding": 131250.00,
                "remaining": 761250.00,
                "paid": 157500.00
            },
            "Interior Design": {
                "total_fee": 1950000.00,
                "outstanding": 0.00,
                "remaining": 1657500.00,
                "paid": 292500.00
            }
        }
    },

    # Page 11
    "25 BK-033": {
        "title": "The Ritz Carlton Reserve, Nusa Dua, Bali, Indonesia",
        "total_fee": 3150000.00,  # LA: 810k + Arch: 1,080k + ID: 1,260k
        "outstanding": 393750.00,  # 101,250 + 135,000 + 157,500
        "remaining": 1890000.00,  # 445,500 + 594,000 + 850,500
        "paid": 1023750.00,  # 263,250 + 351,000 + 409,500
        "disciplines": ["Landscape Architectural", "Architectural", "Interior Design"],
        "breakdown": {
            "Landscape Architectural": {
                "total_fee": 810000.00,
                "outstanding": 101250.00,
                "remaining": 445500.00,
                "paid": 263250.00
            },
            "Architectural": {
                "total_fee": 1080000.00,
                "outstanding": 135000.00,
                "remaining": 594000.00,
                "paid": 351000.00
            },
            "Interior Design": {
                "total_fee": 1260000.00,
                "outstanding": 157500.00,
                "remaining": 850500.00,
                "paid": 409500.00
            }
        }
    },

    "25 BK-040": {
        "title": "The Ritz Carlton Reserve, Nusa Dua, Bali, Indonesia - Branding Consultancy Service",
        "total_fee": 125000.00,
        "outstanding": 0.00,
        "remaining": 93750.00,
        "paid": 31250.00,
        "disciplines": ["Branding Consultancy"]
    },
}

# PDF Footer Totals from Page 11
PDF_GRAND_TOTALS = {
    "total_fee": 66520603.00,
    "outstanding": 5903166.25,
    "remaining": 32803726.13,  # Note: This should be "remaining" not "remaining"
    "paid": 27971210.63
}

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

def compare_projects():
    """Compare PDF projects with database projects"""
    db_projects = get_database_projects()

    print("="*150)
    print("COMPREHENSIVE PDF vs DATABASE VERIFICATION REPORT")
    print("="*150)
    print()

    # Calculate totals
    pdf_total = sum(p["total_fee"] for p in PDF_PROJECTS.values())
    pdf_outstanding_total = sum(p["outstanding"] for p in PDF_PROJECTS.values())
    pdf_remaining_total = sum(p["remaining"] for p in PDF_PROJECTS.values())
    pdf_paid_total = sum(p["paid"] for p in PDF_PROJECTS.values())

    print(f"SUMMARY")
    print(f"-"*150)
    print(f"Total Projects in PDF:      {len(PDF_PROJECTS)}")
    print(f"Total Projects in Database: {len(db_projects)}")
    print()

    # Header
    print(f"{'Project Code':<15} {'Description':<50} {'PDF Total':<15} {'DB Total':<15} {'Match?':<8} {'Difference':<15}")
    print(f"-"*150)

    matches = []
    mismatches = []
    pdf_only = []
    db_only = []

    # Compare each PDF project with database
    for project_code, pdf_data in sorted(PDF_PROJECTS.items()):
        pdf_total_fee = pdf_data["total_fee"]
        pdf_title = pdf_data["title"][:47] + "..." if len(pdf_data["title"]) > 50 else pdf_data["title"]

        if project_code in db_projects:
            db_total_fee = db_projects[project_code]["total_fee"]
            difference = pdf_total_fee - db_total_fee

            if abs(difference) < 0.01:  # Match (within 1 cent)
                match_status = "✓"
                matches.append(project_code)
            else:
                match_status = "✗"
                mismatches.append({
                    "code": project_code,
                    "title": pdf_title,
                    "pdf_total": pdf_total_fee,
                    "db_total": db_total_fee,
                    "difference": difference
                })

            print(f"{project_code:<15} {pdf_title:<50} {format_currency(pdf_total_fee):<15} {format_currency(db_total_fee):<15} {match_status:<8} {format_currency(difference):<15}")
        else:
            pdf_only.append({
                "code": project_code,
                "title": pdf_title,
                "total_fee": pdf_total_fee
            })
            print(f"{project_code:<15} {pdf_title:<50} {format_currency(pdf_total_fee):<15} {'N/A':<15} {'✗':<8} {'IN PDF ONLY':<15}")

    # Check for projects in database but not in PDF
    for project_code, db_data in sorted(db_projects.items()):
        if project_code not in PDF_PROJECTS:
            db_only.append({
                "code": project_code,
                "title": db_data["title"],
                "total_fee": db_data["total_fee"]
            })

    print()
    print("="*150)
    print("DETAILED COMPARISON RESULTS")
    print("="*150)
    print()

    # Matching Projects
    print(f"MATCHING PROJECTS: {len(matches)}")
    print(f"-"*150)
    for code in matches:
        pdf_data = PDF_PROJECTS[code]
        db_data = db_projects[code]
        print(f"  ✓ {code}: {pdf_data['title']}")
        print(f"    Total Fee: {format_currency(pdf_data['total_fee'])} (PDF) = {format_currency(db_data['total_fee'])} (DB)")
    print()

    # Mismatched Projects
    print(f"MISMATCHED PROJECTS: {len(mismatches)}")
    print(f"-"*150)
    for mismatch in mismatches:
        print(f"  ✗ {mismatch['code']}: {mismatch['title']}")
        print(f"    PDF Total:  {format_currency(mismatch['pdf_total'])}")
        print(f"    DB Total:   {format_currency(mismatch['db_total'])}")
        print(f"    Difference: {format_currency(mismatch['difference'])} {'(PDF > DB)' if mismatch['difference'] > 0 else '(DB > PDF)'}")
        print()

    # Projects in PDF only
    print(f"PROJECTS IN PDF BUT NOT IN DATABASE: {len(pdf_only)}")
    print(f"-"*150)
    for proj in pdf_only:
        print(f"  • {proj['code']}: {proj['title']}")
        print(f"    Total Fee: {format_currency(proj['total_fee'])}")
    print()

    # Projects in Database only
    print(f"PROJECTS IN DATABASE BUT NOT IN PDF: {len(db_only)}")
    print(f"-"*150)
    for proj in db_only:
        print(f"  • {proj['code']}: {proj['title']}")
        print(f"    Total Fee: {format_currency(proj['total_fee'])}")
    print()

    # Grand Totals Verification
    print("="*150)
    print("GRAND TOTALS VERIFICATION")
    print("="*150)
    print()

    # Calculate database total
    db_total = sum(p["total_fee"] for p in db_projects.values() if p["total_fee"])

    print(f"{'Category':<30} {'PDF Total':<20} {'Calculated Total':<20} {'PDF Footer':<20} {'Match?':<10}")
    print(f"-"*150)
    print(f"{'Total Fee':<30} {format_currency(pdf_total):<20} {format_currency(db_total):<20} {format_currency(PDF_GRAND_TOTALS['total_fee']):<20} {'✓' if abs(pdf_total - PDF_GRAND_TOTALS['total_fee']) < 0.01 else '✗':<10}")
    print(f"{'Outstanding':<30} {format_currency(pdf_outstanding_total):<20} {'N/A':<20} {format_currency(PDF_GRAND_TOTALS['outstanding']):<20} {'✓' if abs(pdf_outstanding_total - PDF_GRAND_TOTALS['outstanding']) < 0.01 else '✗':<10}")
    print(f"{'Remaining':<30} {format_currency(pdf_remaining_total):<20} {'N/A':<20} {format_currency(PDF_GRAND_TOTALS['remaining']):<20} {'✓' if abs(pdf_remaining_total - PDF_GRAND_TOTALS['remaining']) < 0.01 else '✗':<10}")
    print(f"{'Paid':<30} {format_currency(pdf_paid_total):<20} {'N/A':<20} {format_currency(PDF_GRAND_TOTALS['paid']):<20} {'✓' if abs(pdf_paid_total - PDF_GRAND_TOTALS['paid']) < 0.01 else '✗':<10}")
    print()

    # Verification
    print(f"PDF Sum Verification: Total Fee ({format_currency(pdf_total)}) = Outstanding ({format_currency(pdf_outstanding_total)}) + Remaining ({format_currency(pdf_remaining_total)}) + Paid ({format_currency(pdf_paid_total)})")
    calculated_sum = pdf_outstanding_total + pdf_remaining_total + pdf_paid_total
    print(f"Calculated: {format_currency(calculated_sum)}")
    print(f"Difference: {format_currency(pdf_total - calculated_sum)}")
    print()

    # Final Summary
    print("="*150)
    print("FINAL SUMMARY")
    print("="*150)
    print(f"Total Projects Analyzed: {len(PDF_PROJECTS)}")
    print(f"  ✓ Matching:            {len(matches)}")
    print(f"  ✗ Mismatched:          {len(mismatches)}")
    print(f"  • In PDF Only:         {len(pdf_only)}")
    print(f"  • In Database Only:    {len(db_only)}")
    print()
    print(f"PDF Grand Total:       {format_currency(PDF_GRAND_TOTALS['total_fee'])}")
    print(f"Calculated PDF Total:  {format_currency(pdf_total)}")
    print(f"Database Total:        {format_currency(db_total)}")
    print()

    if len(mismatches) == 0 and len(pdf_only) == 0:
        print("✓ VERIFICATION PASSED: All projects match!")
    else:
        print("✗ VERIFICATION FAILED: Discrepancies found.")
        print()
        print("ACTION REQUIRED:")
        if len(mismatches) > 0:
            print(f"  • Fix {len(mismatches)} mismatched project(s)")
        if len(pdf_only) > 0:
            print(f"  • Add {len(pdf_only)} missing project(s) to database")
        if len(db_only) > 0:
            print(f"  • Review {len(db_only)} project(s) in database but not in PDF")

    print()

    return {
        "matches": matches,
        "mismatches": mismatches,
        "pdf_only": pdf_only,
        "db_only": db_only
    }

if __name__ == "__main__":
    results = compare_projects()

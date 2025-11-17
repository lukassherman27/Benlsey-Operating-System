#!/usr/bin/env python3
"""
Populate team_members table with employee data extracted from schedule PDFs
"""

import sqlite3

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# Team members extracted from the November 2025 Thailand schedule PDF
THAILAND_TEAM = [
    # Architecture Team
    ("Bang", "Bangkok", "Architecture"),
    ("Eclair", "Bangkok", "Architecture"),
    ("Fyi", "Bangkok", "Architecture"),
    ("Mick", "Bangkok", "Architecture"),
    ("Noon", "Bangkok", "Architecture"),
    ("Sprite", "Bangkok", "Architecture"),
    ("Ple", "Bangkok", "Architecture"),
    ("Suwit", "Bangkok", "Architecture"),
    ("Tom", "Bangkok", "Architecture"),
    ("Chai", "Bangkok", "Architecture"),
    ("Jack-BD", "Bangkok", "Architecture"),
    ("Leng", "Bangkok", "Architecture"),
    ("Spot", "Bangkok", "Architecture"),
    ("Wut", "Bangkok", "Architecture"),
    ("Eax", "Bangkok", "Architecture"),
    ("Por", "Bangkok", "Architecture"),
    ("Gawow", "Bangkok", "Architecture"),
    ("Thong", "Bangkok", "Architecture"),
    ("Tu", "Bangkok", "Architecture"),
    ("Poa", "Bangkok", "Architecture"),
    ("Tone", "Bangkok", "Architecture"),
    ("Arm", "Bangkok", "Architecture"),
    ("Cin", "Bangkok", "Architecture"),
    ("Davin", "Bangkok", "Architecture"),

    # Interior Team
    ("Aey", "Bangkok", "Interior"),
    ("Earn 1", "Bangkok", "Interior"),
    ("Earn 2", "Bangkok", "Interior"),
    ("Gio", "Bangkok", "Interior"),
    ("Jal", "Bangkok", "Interior"),
    ("Kae", "Bangkok", "Interior"),
    ("May", "Bangkok", "Interior"),
    ("Mum", "Bangkok", "Interior"),
    ("Nile", "Bangkok", "Interior"),
    ("Ohm", "Bangkok", "Interior"),
    ("Pui", "Bangkok", "Interior"),
    ("Ord", "Bangkok", "Interior"),
    ("Fah", "Bangkok", "Interior"),
    ("Woey", "Bangkok", "Interior"),
    ("Ai", "Bangkok", "Interior"),
    ("Am", "Bangkok", "Interior"),
    ("Aood", "Bangkok", "Interior"),  # Team lead
    ("Priaw", "Bangkok", "Interior"),
    ("Wyn", "Bangkok", "Interior"),
    ("Aubrey", "Bangkok", "Interior"),
    ("Oat", "Bangkok", "Interior"),
    ("Phu", "Bangkok", "Interior"),
    ("Nut", "Bangkok", "Interior"),
    ("Ing-On", "Bangkok", "Interior"),
    ("Kuk", "Bangkok", "Interior"),

    # Landscape Team
    ("Charn", "Bangkok", "Landscape"),
    ("Kaow", "Bangkok", "Landscape"),
    ("Kuad", "Bangkok", "Landscape"),
    ("Man", "Bangkok", "Landscape"),
    ("Moo", "Bangkok", "Landscape"),  # Team lead
    ("Phong", "Bangkok", "Landscape"),
    ("Phot", "Bangkok", "Landscape"),
    ("Teay", "Bangkok", "Landscape"),
]

# Team members from Bali schedule PDF (September)
BALI_TEAM = [
    # Interior Team
    ("Anastasia", "Bali", "Interior"),
    ("Fika", "Bali", "Interior"),
    ("Irma", "Bali", "Interior"),
    ("Julio", "Bali", "Interior"),
    ("Kiko", "Bali", "Interior"),
    ("Rahadi", "Bali", "Interior"),
    ("Rahma Ayu", "Bali", "Interior"),
    ("Reynetha", "Bali", "Interior"),
    ("Trishna", "Bali", "Interior"),
    ("Dely", "Bali", "Interior"),
    ("Hans", "Bali", "Interior"),
    ("Dyah", "Bali", "Interior"),
    ("Reyhan", "Bali", "Interior"),
    ("Tika", "Bali", "Interior"),
    ("Wayan", "Bali", "Interior"),
    ("Putu A.", "Bali", "Interior"),
    ("Rinny", "Bali", "Interior"),

    # Artwork Team
    ("Sarjana", "Bali", "Artwork"),
    ("Yupita", "Bali", "Artwork"),

    # Architecture Team
    ("Bhumi", "Bali", "Architecture"),
    ("Putu", "Bali", "Architecture"),
    ("Rani", "Bali", "Architecture"),
    ("Cok Gung", "Bali", "Architecture"),
    ("Desy", "Bali", "Architecture"),
    ("Ega", "Bali", "Architecture"),

    # Landscape Team
    ("Akbar", "Bali", "Landscape"),
    ("Andri", "Bali", "Landscape"),
    ("Cenik", "Bali", "Landscape"),
    ("Darma", "Bali", "Landscape"),
    ("Nopri", "Bali", "Landscape"),
    ("Rossi", "Bali", "Landscape"),
    ("Sapta", "Bali", "Landscape"),
    ("Agung", "Bali", "Landscape"),
    ("Awan", "Bali", "Landscape"),
    ("Juli", "Bali", "Landscape"),
]


def populate_team_members():
    """Populate team_members table with employee data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    all_team = THAILAND_TEAM + BALI_TEAM

    print(f"Inserting {len(all_team)} team members...")

    inserted = 0
    skipped = 0

    for nickname, office, discipline in all_team:
        try:
            # Generate email from nickname (simplified)
            email = f"{nickname.lower().replace(' ', '')}@bensley.com"

            cursor.execute("""
                INSERT INTO team_members (nickname, full_name, email, office, discipline, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (nickname, nickname, email, office, discipline))

            inserted += 1
            print(f"  ✓ {nickname} ({office} - {discipline})")

        except sqlite3.IntegrityError:
            skipped += 1
            print(f"  - {nickname} (already exists)")

    conn.commit()
    conn.close()

    print(f"\n✅ Done! Inserted {inserted} members, skipped {skipped} duplicates")
    print(f"Total team members in database: {inserted + skipped}")


if __name__ == "__main__":
    populate_team_members()

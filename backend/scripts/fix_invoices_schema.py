#!/usr/bin/env python3
"""
Fix invoices table schema to allow multiple line items per invoice number
"""

import sqlite3

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

def fix_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Fixing invoices table schema...")

    # Step 1: Create new table without UNIQUE constraint on invoice_number
    print("  Creating new invoices table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices_new (
          invoice_id              INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id              INTEGER,
          invoice_number          TEXT,
          description             TEXT,
          invoice_date            DATE,
          due_date                DATE,
          invoice_amount          REAL,
          payment_amount          REAL,
          payment_date            DATE,
          status                  TEXT,
          notes                   TEXT,
          source_ref              TEXT,
          discipline              TEXT,
          phase                   TEXT,
          FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    """)

    # Step 2: Copy existing data
    print("  Copying existing data...")
    cursor.execute("""
        INSERT INTO invoices_new
        SELECT * FROM invoices
    """)

    # Step 3: Drop old table
    print("  Dropping old table...")
    cursor.execute("DROP TABLE invoices")

    # Step 4: Rename new table
    print("  Renaming new table...")
    cursor.execute("ALTER TABLE invoices_new RENAME TO invoices")

    # Step 5: Recreate indexes (but not UNIQUE)
    print("  Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_project ON invoices(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)")

    conn.commit()
    conn.close()

    print("Schema fixed successfully!")

if __name__ == "__main__":
    fix_schema()

#!/usr/bin/env python3
"""Interactive invoice reconciliation tool.

Usage:
    python scripts/reconcile_invoices.py --db /path/to/bensley_master.db [--log reports/invoice_updates.json]

Lets the user page through invoices, verify fields, and update status/payment info.
"""

import argparse
import json
import os
import sqlite3
from datetime import datetime

def fetch_invoices(conn, where_clause="", params=None):
    params = params or []
    query = f"""
        SELECT i.invoice_id, p.project_code, p.project_name,
               i.invoice_number, i.invoice_date, i.due_date,
               i.invoice_amount, i.payment_amount, i.payment_date,
               i.status, i.phase, i.discipline, i.description
        FROM invoices i
        LEFT JOIN projects p ON i.project_id = p.proposal_id
        {('WHERE ' + where_clause) if where_clause else ''}
        ORDER BY p.project_code, i.invoice_date
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    return cur.fetchall()

def update_invoice(conn, invoice_id, field, value):
    cur = conn.cursor()
    cur.execute(f"UPDATE invoices SET {field} = ? WHERE invoice_id = ?", (value, invoice_id))
    conn.commit()

def interactive_session(conn, log_path):
    invoices = fetch_invoices(conn)
    total = len(invoices)
    print(f"Loaded {total} invoices. Commands: next (n), prev (p), set FIELD VALUE, status list, help, quit (q)")
    idx = 0
    updates = []
    while 0 <= idx < total:
        inv = invoices[idx]
        print("\n=== Invoice {}/{} ===".format(idx + 1, total))
        print(f"Project: {inv['project_code']} – {inv['project_name']}")
        print(f"Invoice#: {inv['invoice_number']}  Phase: {inv['phase']}  Discipline: {inv['discipline']}")
        print(f"Invoice Date: {inv['invoice_date']}  Due: {inv['due_date']}")
        print(f"Invoice Amount: {inv['invoice_amount']}  Payment Amount: {inv['payment_amount']}  Payment Date: {inv['payment_date']}")
        print(f"Status: {inv['status']}  Description: {inv['description']}")
        cmd = input("Command: ").strip()
        if cmd in ("next", "n", ""):
            idx += 1
        elif cmd in ("prev", "p"):
            idx = max(0, idx - 1)
        elif cmd.startswith("set "):
            _, field, *value = cmd.split()
            value = " ".join(value)
            confirm = input(f"Set {field} = '{value}'? (y/n) ").strip().lower()
            if confirm == "y":
                update_invoice(conn, inv['invoice_id'], field, value)
                updates.append({"invoice_id": inv['invoice_id'], "field": field, "value": value, "timestamp": datetime.utcnow().isoformat()})
                print("Updated.")
        elif cmd == "status list":
            outstanding = fetch_invoices(conn, "i.status = ?", ["Outstanding"])
            print("Outstanding invoices:")
            for row in outstanding:
                print(f"  {row['project_code']} | {row['invoice_number']} | {row['invoice_amount']} | {row['phase']}")
        elif cmd == "help":
            print("Commands:\n  next/n  -> next invoice\n  prev/p  -> previous invoice\n  set FIELD VALUE -> update field\n  status list -> show outstanding invoices\n  quit/q -> exit")
        elif cmd in ("quit", "q"):
            break
        else:
            print("Unknown command; type 'help' for options.")
    if updates:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as fh:
            json.dump(updates, fh, indent=2)
        print(f"Saved {len(updates)} updates to {log_path}.")

def main():
    parser = argparse.ArgumentParser(description="Invoice reconciliation CLI")
    parser.add_argument("--db", required=True, help="Path to bensley_master.db")
    parser.add_argument("--log", default="reports/invoice_updates.json", help="Where to store JSON change log")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        raise FileNotFoundError(args.db)

    conn = sqlite3.connect(args.db)
    try:
        interactive_session(conn, args.log)
    finally:
        conn.close()

if __name__ == "__main__":
    main()

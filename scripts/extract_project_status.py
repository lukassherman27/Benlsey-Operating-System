#!/usr/bin/env python3
"""Extract invoice rows from the Project Status PDF into CSV.

This parser is heuristic-based: it reads each project block, collects invoice numbers,
amounts, and payment dates, then zips them together. Manual review is still required,
but the resulting CSV is easier to audit/import.
"""
import argparse
import csv
import re
from pathlib import Path

from pdfminer.high_level import extract_text

HEADER_RE = re.compile(r"^(?P<idx>\d+)\s+(?P<code>\d+\s+BK-\d+)\s*$")
INVOICE_RE = re.compile(r"^[A-Z]\d{2}-\d{3}[A-Z]?(&[A-Z])?$")
AMOUNT_RE = re.compile(r"^[0-9][0-9,]*\.?[0-9]*$")
DATE_RE = re.compile(r"^\d{1,2}-[A-Za-z]{3}-\d{2}$")
DESCRIPTION_HEADERS = {"project title", "description"}


def normalize_amount(value: str) -> str:
    return value.replace(",", "")


def flush_block(block, results, page_no):
    if not block["invoice_numbers"]:
        return
    invoices = block["invoice_numbers"]
    amounts = block["amounts"]
    payments = block["payments"]
    descs = block["descriptions"]
    max_len = max(len(invoices), len(amounts), len(payments))
    for idx in range(max_len):
        results.append(
            {
                "project_code": block["code"],
                "project_name": block["name"],
                "invoice_number": invoices[idx] if idx < len(invoices) else "",
                "invoice_amount": normalize_amount(amounts[idx]) if idx < len(amounts) else "",
                "payment_date": payments[idx] if idx < len(payments) else "",
                "description": descs[idx] if idx < len(descs) else "",
                "pdf_page": page_no,
            }
        )


def parse_pdf(pdf_path: Path):
    text = extract_text(str(pdf_path))
    results = []
    current = {"code": "", "name": "", "invoice_numbers": [], "amounts": [], "payments": [], "descriptions": []}
    page_no = 1
    capture_name = False
    last_text = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Page") and "out of" in line:
            flush_block(current, results, page_no)
            current = {"code": "", "name": "", "invoice_numbers": [], "amounts": [], "payments": [], "descriptions": []}
            page_no += 1
            capture_name = False
            continue
        m = HEADER_RE.match(line)
        if m:
            flush_block(current, results, page_no)
            current = {"code": m.group("code"), "name": "", "invoice_numbers": [], "amounts": [], "payments": [], "descriptions": []}
            capture_name = False
            last_text = ""
            continue
        if line.lower() in DESCRIPTION_HEADERS:
            capture_name = (line.lower() == "project title")
            continue
        if capture_name and not current["name"]:
            current["name"] = line
            capture_name = False
            continue
        if INVOICE_RE.match(line):
            current["invoice_numbers"].append(line)
            current["descriptions"].append(last_text)
        elif AMOUNT_RE.match(line):
            current["amounts"].append(line)
        elif DATE_RE.match(line):
            current["payments"].append(line)
        last_text = line
    flush_block(current, results, page_no)
    return results


def write_csv(rows, csv_path: Path):
    fieldnames = ["project_code", "project_name", "invoice_number", "invoice_amount", "payment_date", "description", "pdf_page"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main():
    parser = argparse.ArgumentParser(description="Extract invoices from Project Status PDF")
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    rows = parse_pdf(Path(args.pdf))
    write_csv(rows, Path(args.csv))
    print(f"Extracted {len(rows)} rows to {args.csv}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
project_creator.py

Create new project with complete folder structure and database entry
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ProjectCreator:
    def __init__(self):
        self.base_path = Path("/home/user/Benlsey-Operating-System/data")
        self.db_path = os.getenv('DATABASE_PATH') or str(self.base_path.parent / "database" / "bensley_master.db")
        self.data_root = self.base_path.parent

    def create_project(self, project_code, project_name, client_name, operator_name=None,
                      contract_value=0, status='active', start_date=None, completion_target=None):
        """Create new project with full structure"""

        # Create folder name
        folder_name = f"{project_code}_{project_name.replace(' ', '_')}"

        # Determine base folder based on status
        if status == 'proposal':
            base_folder = self.base_path / "03_PROPOSALS"
        elif status == 'active':
            base_folder = self.base_path / "04_ACTIVE_PROJECTS"
        elif status == 'legal':
            base_folder = self.base_path / "05_LEGAL_DISPUTES"
        elif status == 'archive':
            base_folder = self.base_path / "06_ARCHIVE"
        else:
            base_folder = self.base_path / "04_ACTIVE_PROJECTS"

        project_path = base_folder / folder_name

        # Check if project already exists
        if project_path.exists():
            print(f"⚠️  Project already exists: {project_code}")
            return None

        print(f"\n🏗️  Creating project: {project_code}")
        print(f"   Path: {project_path}")

        # Create folder structure
        folders = [
            "01_CONTRACT",
            "02_INVOICING/invoices_sent",
            "02_INVOICING/payment_receipts",
            "03_DESIGN/architecture/revisions",
            "03_DESIGN/architecture/current",
            "03_DESIGN/interiors",
            "03_DESIGN/landscape",
            "04_SCHEDULING/forward_schedule",
            "04_SCHEDULING/daily_reports/by_staff",
            "04_SCHEDULING/daily_reports/by_date",
            "04_SCHEDULING/milestones",
            "05_CORRESPONDENCE/client_emails",
            "05_CORRESPONDENCE/operator_emails",
            "05_CORRESPONDENCE/consultant_emails",
            "06_SUBMISSIONS",
            "07_RFIS",
            "08_MEETINGS",
            "09_PHOTOS"
        ]

        for folder in folders:
            (project_path / folder).mkdir(parents=True, exist_ok=True)
            print(f"   ✓ {folder}")

        # Create metadata.json
        metadata = {
            "project_code": project_code,
            "project_name": project_name,
            "client": client_name,
            "operator": operator_name,
            "contract_value": contract_value,
            "start_date": start_date or datetime.now().strftime("%Y-%m-%d"),
            "completion_target": completion_target,
            "current_phase": "Initiation",
            "team_lead": None,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        with open(project_path / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"   ✓ metadata.json")

        # Create billing_schedule.json
        billing_schedule = {
            "project_code": project_code,
            "total_contract_value": contract_value,
            "paid_to_date": 0,
            "outstanding": contract_value,
            "payment_schedule": [],
            "next_invoice_date": None,
            "notes": ""
        }

        with open(project_path / "02_INVOICING" / "billing_schedule.json", 'w') as f:
            json.dump(billing_schedule, f, indent=2)
        print(f"   ✓ billing_schedule.json")

        # Add to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO projects
            (project_code, project_name, client_name, value, status, base_path, current_phase)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (project_code, project_name, client_name, contract_value, status,
              str(project_path), "Initiation"))

        conn.commit()
        project_id = cursor.lastrowid
        conn.close()

        print(f"\n✅ Project created successfully!")
        print(f"   Database ID: {project_id}")
        print(f"   Folder: {project_path}")

        return project_id, project_path

def main():
    print("="*70)
    print("BENSLEY PROJECT CREATOR")
    print("="*70)

    creator = ProjectCreator()

    # Get project details
    print("\nEnter project details:")
    project_code = input("Project Code (e.g., BK-001): ").strip()
    project_name = input("Project Name: ").strip()
    client_name = input("Client Name (who pays): ").strip()
    operator_name = input("Operator/Brand (optional): ").strip() or None

    contract_value_input = input("Contract Value (default 0): ").strip()
    contract_value = float(contract_value_input) if contract_value_input else 0

    print("\nStatus:")
    print("  1. Proposal")
    print("  2. Active")
    print("  3. Legal")
    print("  4. Archive")
    status_choice = input("Choose (default 2): ").strip() or "2"

    status_map = {
        "1": "proposal",
        "2": "active",
        "3": "legal",
        "4": "archive"
    }
    status = status_map.get(status_choice, "active")

    # Create project
    project_id, project_path = creator.create_project(
        project_code, project_name, client_name, operator_name,
        contract_value, status
    )

    print(f"\n🎉 Ready to use!")
    print(f"   Add files to: {project_path}")

if __name__ == '__main__':
    main()

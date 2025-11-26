# Getting Started with Bensley Intelligence Platform

Welcome! This guide will get you up and running in 10 minutes.

## Quick Start (Easiest Way)

### 1. Clone the Repository

```bash
# On your computer, navigate to where you want the project
cd C:\Users\YourName\OneDrive\Bensley  # or wherever you want it

# Clone from GitHub
git clone https://github.com/lukassherman27/Benlsey-Operating-System.git
cd Benlsey-Operating-System
```

### 2. Run the Quick Start Script

```bash
# This does everything: installs dependencies, sets up database, configures environment
python quickstart.py
```

The script will ask you a few questions:
- Email server credentials (tmail.bensley.com)
- OpenAI API key (optional - can skip)
- Whether to create an example project

That's it! You're ready to go.

---

## What You Can Do Now

### Import Existing Projects from Excel

```bash
# Activate virtual environment first
venv\Scripts\activate              # Windows
source venv/bin/activate           # Mac/Linux

# Import projects
python backend/services/excel_importer.py --file "path/to/your/projects.xlsx"
```

Your Excel should have columns like:
- Project Code (BK-001)
- Project Name
- Client Name (who pays)
- Operator Name (hotel brand)
- Contract Value
- Status (active/proposal/completed)

### Organize Existing Files

```bash
# Scan your old project folders and see where files should go
python backend/services/file_organizer.py --scan "C:\Old_Projects" --dry-run

# Actually organize them (copies by default)
python backend/services/file_organizer.py --scan "C:\Old_Projects"

# Or move instead of copy
python backend/services/file_organizer.py --scan "C:\Old_Projects" --move
```

The tool will:
- Find project codes in filenames (BK-001, BK-123, etc.)
- Identify file types (contracts, invoices, drawings, photos)
- Put them in the right folders automatically

### Sync Emails from tmail

```bash
# Download all emails and attachments
python backend/services/email_importer.py

# Or just new emails since last sync
python backend/services/email_importer.py --incremental
```

Emails go to: `data/07_EMAILS/`
- raw/ - Original email files
- processed/ - Extracted data
- attachments/ - All attachments

### Create New Projects

```bash
# Interactive mode - it will ask you for details
python backend/services/project_creator.py
```

This creates the complete folder structure:
```
data/04_ACTIVE_PROJECTS/BK-XXX_Project_Name/
├── 01_CONTRACT/
├── 02_INVOICING/
├── 03_DESIGN/
├── 04_SCHEDULING/
│   ├── forward_schedule/      # What managers assign
│   └── daily_reports/         # What staff actually did (with photos)
├── 05_CORRESPONDENCE/
├── 06_SUBMISSIONS/
├── 07_RFIS/
├── 08_MEETINGS/
├── 09_PHOTOS/
└── metadata.json
```

### Start the API (Optional)

```bash
# Start the REST API server
python -m uvicorn backend.api.main:app --reload

# Open in browser: http://localhost:8000/docs
```

You can:
- See all projects: GET /projects
- Get project details: GET /projects/{code}
- See metrics: GET /metrics
- Search emails: GET /emails/search

---

## Understanding the Structure

### Where Everything Lives

```
Benlsey-Operating-System/
├── quickstart.py              # Run this first!
├── .env                       # Your configuration (created by quickstart)
│
├── data/                      # All project files
│   ├── 01_CLIENTS/           # Who pays you
│   ├── 02_OPERATORS/         # Hotel brands (Rosewood, etc.)
│   ├── 03_PROPOSALS/         # Not signed yet
│   ├── 04_ACTIVE_PROJECTS/   # Signed contracts ← Most action here
│   ├── 05_LEGAL_DISPUTES/    # Problem projects
│   ├── 06_ARCHIVE/           # Completed
│   ├── 07_EMAILS/            # All emails & attachments
│   └── 08_TEMPLATES/         # Reusable documents
│
├── database/
│   ├── bensley_master.db     # SQLite database (all your data)
│   └── migrations/           # Database schema updates
│
├── backend/
│   ├── api/                  # REST API
│   ├── core/                 # Your old 30 scripts (moved here)
│   └── services/             # New tools
│       ├── project_creator.py
│       ├── excel_importer.py
│       ├── file_organizer.py
│       └── email_importer.py
│
└── venv/                     # Python environment (created by quickstart)
```

### Important Files in Each Project

Every project has:

**metadata.json** - Core project info
```json
{
  "project_code": "BK-001",
  "project_name": "Luxury Resort",
  "client": "Developer Corp",
  "operator": "Rosewood Hotels",
  "contract_value": 2500000,
  "status": "active"
}
```

**02_INVOICING/billing_schedule.json** - Payment tracking
```json
{
  "total_contract_value": 2500000,
  "paid_to_date": 1500000,
  "outstanding": 1000000,
  "payment_schedule": [...]
}
```

**04_SCHEDULING/forward_schedule/** - What managers plan
**04_SCHEDULING/daily_reports/** - What actually happened (with photos)

---

## Daily Workflows

### Project Manager Creating Weekly Schedule

1. Open: `data/04_ACTIVE_PROJECTS/BK-XXX/04_SCHEDULING/forward_schedule/`
2. Create or edit: `weekly_plan.json`
3. Assign tasks to staff for the week

### Staff Submitting Daily Work Report

1. Staff emails Bill & Brian with:
   - What they worked on today
   - Hours spent
   - Photos of progress
   - Issues encountered
   - Tomorrow's plan

2. System automatically:
   - Extracts info from email
   - Saves to: `04_SCHEDULING/daily_reports/by_date/YYYY-MM-DD_daily_reports.json`
   - Stores photos in project folder
   - Updates database

### Creating a New Project

```bash
python backend/services/project_creator.py
```

Follow prompts, then:
1. Add contract to: `01_CONTRACT/`
2. Set up billing schedule: `02_INVOICING/billing_schedule.json`
3. Create weekly plan: `04_SCHEDULING/forward_schedule/`

---

## Common Tasks

### Check Database

Use DB Browser for SQLite (free tool):
1. Download from: https://sqlitebrowser.org/
2. Open: `database/bensley_master.db`
3. Browse tables: projects, emails, invoices, etc.

### Backup Everything

Your data lives in two places:
1. **Files:** `data/` folder (4GB typical)
2. **Database:** `database/bensley_master.db` (100MB typical)

Backup both:
```bash
# Backup files
xcopy data backup_data_2024-11-12 /E /I    # Windows
cp -r data backup_data_2024-11-12           # Mac/Linux

# Backup database
copy database\bensley_master.db database\bensley_master_backup_2024-11-12.db
```

Or just push to OneDrive/Dropbox if that's where you cloned it.

### Update the System

```bash
# Pull latest changes from GitHub
git pull origin main

# Update dependencies if requirements.txt changed
pip install -r requirements.txt --upgrade

# Run any new database migrations
python database/run_migrations.py
```

---

## Troubleshooting

### "Module not found" errors

```bash
# Make sure virtual environment is activated
venv\Scripts\activate              # Windows
source venv/bin/activate           # Mac/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### Can't connect to email server

- Check you're on office network (or VPN)
- Verify credentials in `.env` file
- Test with: `python backend/services/email_importer.py`

### Database locked error

- Close DB Browser for SQLite if open
- Only one program can write at a time

### Excel import fails

Check your Excel has these columns (case-insensitive):
- Project Code or Code
- Project Name or Name
- Client or Client Name
- Status (optional - defaults to "active")

---

## Next Steps

1. **Import your existing projects** from Excel
2. **Organize your existing files** with file_organizer.py
3. **Sync historical emails** from tmail
4. **Create templates** in `data/08_TEMPLATES/`
5. **Set up daily email sync** (scheduled task)

---

## Getting Help

### Documentation
- **DEPLOYMENT_GUIDE.md** - Detailed setup instructions
- **FOUNDATION_BUILT.md** - Architecture and database schema
- **WHAT_DID_WE_BUILD.md** - Plain English explanation
- **data/README.md** - File organization reference

### Tools Reference
```bash
# Project creation
python backend/services/project_creator.py

# Excel import
python backend/services/excel_importer.py --file projects.xlsx

# File organization
python backend/services/file_organizer.py --scan /old/projects

# Email sync
python backend/services/email_importer.py

# Start API
python -m uvicorn backend.api.main:app --reload
```

---

## Tips

✅ **Use project codes consistently** - BK-001, BK-002, etc.
✅ **Daily work reports are critical** - Photos show progress
✅ **Keep metadata.json updated** - This drives the system
✅ **Backup regularly** - Data + Database
✅ **Use templates** - Create once, reuse many times

❌ **Don't skip folder structure** - Every project needs all folders
❌ **Don't manually edit database** - Use Python scripts
❌ **Don't mix old and new systems** - Migrate fully

---

**Ready to go?** Run `python quickstart.py` and you'll be up in minutes! 🚀

# Bensley Intelligence Platform - Deployment Guide

## Getting This Running on Your Computer

This guide walks you through setting up the platform on your local machine or OneDrive, connecting your email server, and populating with real data.

---

## Step 1: Get the Code on Your Computer

### Option A: OneDrive (Recommended for backup)
```bash
# On your computer, navigate to your OneDrive folder
cd "C:\Users\YourName\OneDrive\Bensley"

# Clone the repository
git clone https://github.com/lukassherman27/Benlsey-Operating-System.git
cd Benlsey-Operating-System
```

### Option B: Local Drive (Faster)
```bash
# Navigate to where you want to work
cd "C:\Bensley"

# Clone the repository
git clone https://github.com/lukassherman27/Benlsey-Operating-System.git
cd Benlsey-Operating-System
```

---

## Step 2: Install Python Environment

### Install Python 3.11+ (if not already installed)
Download from: https://www.python.org/downloads/

### Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Step 3: Configure Your Environment

### Create .env file
```bash
# Copy the example
cp .env.example .env

# Edit .env with your paths (use Notepad or VS Code)
```

### Edit .env with YOUR paths:
```ini
# Database location - where SQLite database will be stored
DATABASE_PATH=C:/Users/YourName/OneDrive/Bensley/Benlsey-Operating-System/database/bensley_master.db

# Data folder - where all project files live
DATA_ROOT_PATH=C:/Users/YourName/OneDrive/Bensley/Benlsey-Operating-System/data

# Email server (your existing tmail setup)
EMAIL_SERVER=tmail.bensley.com
EMAIL_PORT=993
EMAIL_USERNAME=lukas@bensley.com
EMAIL_PASSWORD=0823356345

# OpenAI (optional - for AI features later)
OPENAI_API_KEY=your-key-here
```

**IMPORTANT:** Use forward slashes `/` in Windows paths, not backslashes `\`

---

## Step 4: Initialize the Database

```bash
# Create fresh database with all tables
python database/init_database.py
```

This creates:
- All core tables (projects, emails, contacts, etc.)
- Business tables (clients, operators, invoices, payments)
- Scheduling tables (staff assignments, daily work logs)
- Sample data (3 example projects)

---

## Step 5: Connect Your Email Server

### Test Email Connection
```bash
# Run the email importer
python backend/services/email_importer.py
```

This will:
1. Connect to tmail.bensley.com:993
2. Scan all folders in your mailbox
3. Download emails to `data/07_EMAILS/raw/`
4. Process and extract project references
5. Store attachments in `data/07_EMAILS/attachments/`

### Set Up Automatic Email Sync (Optional)
Create a scheduled task (Windows) or cron job (Mac/Linux) to run daily:
```bash
python backend/services/email_importer.py --incremental
```

---

## Step 6: Import Your Existing Projects

### From Excel Files

You mentioned you have project lists in Excel. Let's import them:

```bash
# Run the Excel importer (we'll create this)
python backend/services/excel_importer.py --file "path/to/your/projects.xlsx"
```

This will:
1. Read your Excel with columns: Project Code, Client, Operator, Contract Value, Status
2. Create folder structure for each project in `data/04_ACTIVE_PROJECTS/`
3. Add entries to database
4. Generate metadata.json for each project

### Manual Project Creation

Or create projects one by one:
```bash
python backend/services/project_creator.py
```

Follow the prompts:
- Project Code: BK-123
- Project Name: New Resort Project
- Client: Who pays (developer/owner)
- Operator: Hotel brand (Rosewood, Mandarin Oriental, etc.)
- Contract Value: 2500000
- Status: active/proposal/archived

This creates complete folder structure:
```
data/04_ACTIVE_PROJECTS/BK-123_New_Resort_Project/
├── 01_CONTRACT/
├── 02_INVOICING/
├── 03_DESIGN/
├── 04_SCHEDULING/
├── 05_CORRESPONDENCE/
├── 06_SUBMISSIONS/
├── 07_RFIS/
├── 08_MEETINGS/
├── 09_PHOTOS/
└── metadata.json
```

---

## Step 7: Connect Your Existing Documents

### If you have existing project folders:

**Option A: Move files into new structure**
```bash
# Example: Moving existing BK-123 files
# From: C:\Old_Projects\BK-123\
# To:   C:\...\data\04_ACTIVE_PROJECTS\BK-123_Project_Name\

# Move contracts
copy "C:\Old_Projects\BK-123\Contracts\*" "data\04_ACTIVE_PROJECTS\BK-123_Project_Name\01_CONTRACT\"

# Move drawings
copy "C:\Old_Projects\BK-123\Drawings\*" "data\04_ACTIVE_PROJECTS\BK-123_Project_Name\03_DESIGN\architecture\current\"

# Move invoices
copy "C:\Old_Projects\BK-123\Invoices\*" "data\04_ACTIVE_PROJECTS\BK-123_Project_Name\02_INVOICING\invoices_sent\"
```

**Option B: Create symbolic links** (keeps files in current location)
```bash
# Windows (run as Administrator)
mklink /D "data\04_ACTIVE_PROJECTS\BK-123_Project_Name\03_DESIGN" "C:\Old_Projects\BK-123\Drawings"

# Mac/Linux
ln -s "/path/to/old/BK-123/Drawings" "data/04_ACTIVE_PROJECTS/BK-123_Project_Name/03_DESIGN"
```

---

## Step 8: Set Up Daily Work Reports

### Email Processing for Daily Reports

Staff emails to Bill & Brian with work updates and photos will be processed automatically.

The system looks for emails:
- **To:** bill@bensley.com, brian@bensley.com
- **Subject:** Contains "daily report" or "work update" or project code
- **Attachments:** Photos of work progress

These get stored in:
```
data/04_ACTIVE_PROJECTS/[PROJECT]/04_SCHEDULING/daily_reports/
├── by_date/
│   └── 2024-11-12_daily_reports.json
└── by_staff/
    └── Designer_1_work_history.json
```

### Forward Schedule

Project managers create weekly plans:
```
data/04_ACTIVE_PROJECTS/[PROJECT]/04_SCHEDULING/forward_schedule/
└── weekly_plan.json
```

---

## Step 9: Start Using the System

### Create Your First Real Project
```bash
python backend/services/project_creator.py
```

### Sync Emails
```bash
python backend/services/email_importer.py
```

### Check the Database
```bash
# Use DB Browser for SQLite (free tool)
# Open: database/bensley_master.db
# Or use Python:
python -c "
from backend.core.database_audit import show_summary
show_summary()
"
```

### Start the API (Optional)
```bash
python -m uvicorn backend.api.main:app --reload

# Open browser: http://localhost:8000/docs
# Test endpoints: /health, /projects, /metrics
```

---

## Common Paths & Files

### Where Everything Lives:

```
Benlsey-Operating-System/
├── .env                          # YOUR configuration
├── database/
│   └── bensley_master.db        # SQLite database (all your data)
├── data/
│   ├── 01_CLIENTS/              # Who pays you
│   ├── 02_OPERATORS/            # Hotel brands
│   ├── 03_PROPOSALS/            # Not signed yet
│   ├── 04_ACTIVE_PROJECTS/      # Signed contracts
│   │   └── BK-XXX_Project/      # Each project folder
│   ├── 05_LEGAL_DISPUTES/       # Problem projects
│   ├── 06_ARCHIVE/              # Completed
│   ├── 07_EMAILS/               # All emails & attachments
│   └── 08_TEMPLATES/            # Reusable documents
├── backend/
│   ├── core/                    # Your old 30 scripts
│   └── services/                # New tools
└── venv/                        # Python environment (local only)
```

---

## Next Steps After Deployment

1. **Import all existing projects** from Excel
2. **Sync all historical emails** from tmail
3. **Organize existing documents** into project folders
4. **Set up daily email sync** (scheduled task)
5. **Train staff** on daily work report format
6. **Start using project_creator.py** for new projects

---

## Troubleshooting

### Email connection fails
```bash
# Test connection
python -c "
import imaplib
mail = imaplib.IMAP4_SSL('tmail.bensley.com', 993)
mail.login('lukas@bensley.com', '0823356345')
print('✅ Connected successfully')
"
```

### Database not found
- Check DATABASE_PATH in .env
- Make sure you ran `python database/init_database.py`

### Import errors
```bash
# Make sure you're in the right directory
cd /path/to/Benlsey-Operating-System

# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

---

## Security Notes

⚠️ **IMPORTANT:**
- Keep `.env` file secure (never commit to git - it's in .gitignore)
- The database contains sensitive client/payment info
- Email attachments may contain confidential designs
- Consider encrypting OneDrive folder if storing there

---

## Getting Help

- Check `FOUNDATION_BUILT.md` for architecture details
- Check `WHAT_DID_WE_BUILD.md` for plain English explanation
- Check `data/README.md` for folder structure reference
- Check individual project `README.md` files for specific workflows

---

**Ready to go?** Start with Step 1 and work through each section. The system will guide you through setup.

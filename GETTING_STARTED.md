# 🚀 GETTING STARTED - Your First 3 Days

This guide will take you from where you are now to a working API in 3 days.

---

## 🎯 TODAY (Day 1) - 2 Hours

### Step 1: Run the Setup Script (10 minutes)

```bash
# Make sure you're in the project directory
cd ~/path/to/Benlsey-Operating-System

# Run the setup script
./setup.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Organize your code structure
- Create .env file from template

### Step 2: Configure Your Environment (15 minutes)

Edit the `.env` file with your actual paths:

```bash
nano .env
```

**REQUIRED changes:**
```bash
# Update this to your actual database path
DATABASE_PATH=/Users/yourname/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db

# Add your OpenAI key (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-actual-key-here
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 3: Move Your Scripts (10 minutes)

Your existing Python scripts need to be in `backend/core/`:

```bash
# They should have been moved by setup.sh, but verify:
ls -la backend/core/

# You should see:
# - email_processor.py
# - pattern_learner.py
# - rfi_tracker.py
# - proposal_status_tracker.py
# - etc.
```

### Step 4: Test the API (15 minutes)

Start the API server:

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Start the server
python3 backend/api/main.py
```

You should see:
```
    ╔══════════════════════════════════════════════════════════╗
    ║   Bensley Intelligence Platform API                      ║
    ╚══════════════════════════════════════════════════════════╝

    🚀 Starting server...
    📡 API:  http://localhost:8000
    📚 Docs: http://localhost:8000/docs
```

### Step 5: Explore the API (30 minutes)

Open your browser to: **http://localhost:8000/docs**

This is the **Swagger UI** - an interactive API documentation.

Try these endpoints:

1. **GET /health** - Check if everything is connected
2. **GET /metrics** - See your business metrics
3. **GET /projects** - List all projects
4. **GET /projects/BK-001** - Get details for a specific project (use your actual project code)

### Step 6: Test with curl (15 minutes)

From another terminal:

```bash
# Check health
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/metrics

# List projects
curl http://localhost:8000/projects

# Get specific project
curl http://localhost:8000/projects/BK-001
```

### Step 7: Review What You Built (15 minutes)

You now have:
- ✅ REST API serving your data
- ✅ Interactive documentation
- ✅ Real-time metrics endpoint
- ✅ Project and email queries
- ✅ Foundation for automation

**🎉 Day 1 Complete!**

---

## 🎯 TOMORROW (Day 2) - 4 Hours

### Step 1: Export Database Schema (30 minutes)

Document your current database structure:

```bash
# Export schema
sqlite3 ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db .schema > database/schema.sql

# Review it
cat database/schema.sql
```

### Step 2: Create Database Service (1 hour)

Create `backend/services/database_service.py`:

```python
import sqlite3
import os
from contextlib import contextmanager

class DatabaseService:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv('DATABASE_PATH')

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_all_projects(self):
        """Get all projects"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY project_id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_project_by_code(self, project_code):
        """Get project by code"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE project_code = ?", (project_code,))
            row = cursor.fetchone()
            return dict(row) if row else None
```

### Step 3: Create Project Service (1 hour)

Create `backend/services/project_service.py`:

```python
from backend.services.database_service import DatabaseService

class ProjectService:
    def __init__(self):
        self.db = DatabaseService()

    def list_projects(self, status=None, limit=50):
        """List projects with optional filters"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM projects"
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY project_id DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_project_details(self, project_code):
        """Get detailed project information with related data"""
        project = self.db.get_project_by_code(project_code)

        if not project:
            return None

        # Get linked emails
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM email_project_links
                WHERE project_id = ?
            """, (project['project_id'],))
            project['email_count'] = cursor.fetchone()[0]

            # Get recent activity
            cursor.execute("""
                SELECT e.date, e.subject, e.sender_email
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE epl.project_id = ?
                ORDER BY e.date DESC
                LIMIT 10
            """, (project['project_id'],))

            project['recent_emails'] = [dict(row) for row in cursor.fetchall()]

        return project

    def get_active_project_count(self):
        """Count active projects"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM projects
                WHERE status IN ('active', 'in-progress', 'ongoing')
            """)
            return cursor.fetchone()[0]
```

### Step 4: Update API to Use Services (30 minutes)

Update `backend/api/main.py` to use your new services:

```python
from backend.services.project_service import ProjectService

project_service = ProjectService()

@app.get("/projects")
async def list_projects(status: Optional[str] = None, limit: int = 50):
    """List all projects"""
    projects = project_service.list_projects(status=status, limit=limit)
    return projects

@app.get("/projects/{project_code}")
async def get_project(project_code: str):
    """Get project details"""
    project = project_service.get_project_details(project_code)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

### Step 5: Test Everything (1 hour)

Restart your API and test all endpoints:

```bash
# Restart API
python3 backend/api/main.py

# Test in another terminal
curl http://localhost:8000/projects
curl http://localhost:8000/projects/BK-001
```

**🎉 Day 2 Complete!**

---

## 🎯 DAY 3 - First Automation (4 Hours)

### Step 1: Install n8n (30 minutes)

```bash
# Install n8n globally
npm install -g n8n

# Set basic authentication
export N8N_BASIC_AUTH_ACTIVE=true
export N8N_BASIC_AUTH_USER=admin
export N8N_BASIC_AUTH_PASSWORD=bensley123

# Start n8n
n8n start
```

Open: **http://localhost:5678**

Login with: admin / bensley123

### Step 2: Create Your First Workflow (1 hour)

In n8n UI:

1. Click "New Workflow"
2. Name it: "Daily Metrics Email"
3. Add nodes:

**Node 1: Schedule Trigger**
- Type: Cron
- Expression: `0 6 * * *` (every day at 6am)

**Node 2: HTTP Request**
- URL: `http://localhost:8000/metrics`
- Method: GET

**Node 3: Function**
- Code:
```javascript
const metrics = $input.first().json;

const message = `
Daily Intelligence Briefing - ${new Date().toDateString()}

📊 BUSINESS METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Active Projects: ${metrics.active_projects}
• Pending RFIs: ${metrics.pending_rfis}
• Proposals In Progress: ${metrics.proposals_in_progress}
• Unprocessed Emails: ${metrics.unprocessed_emails}

Processed today: ${metrics.emails_processed_today} emails

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
View dashboard: http://localhost:3000
`;

return { subject: 'Daily Briefing', body: message };
```

**Node 4: Send Email** (or Slack, or whatever you prefer)
- Configure with your email settings

### Step 3: Test Workflow (30 minutes)

1. Click "Execute Workflow" to test
2. Check each node's output
3. Verify email is sent
4. Activate workflow for daily runs

### Step 4: Create Second Workflow - Email Processor (1 hour)

Create: "Process Incoming Emails"

**Node 1: Webhook**
- Method: POST
- Path: `process-email`

**Node 2: HTTP Request**
- URL: `http://localhost:8000/emails/process`
- Method: POST
- Body: `{{ $json }}`

**Node 3: Condition**
- If confidence > 0.8, send to project manager
- Else, flag for manual review

### Step 5: Document Your Setup (1 hour)

Create `docs/API_USAGE.md`:

```markdown
# API Usage Guide

## Authentication
Currently no authentication required for local development.
Production will use API keys.

## Key Endpoints

### GET /metrics
Returns real-time business metrics

### GET /projects
List all projects

### GET /projects/{code}/emails
Get emails for specific project

## Examples
[Add your working curl examples]
```

**🎉 Day 3 Complete!**

---

## ✅ What You Have Now (After 3 Days)

- ✅ **Working REST API** serving all your data
- ✅ **Interactive documentation** at /docs
- ✅ **Database services** for clean data access
- ✅ **First automation** (daily digest)
- ✅ **n8n installed** and configured
- ✅ **Foundation for dashboard** (API ready)

---

## 🎯 NEXT WEEK - Dashboard

Follow **Week 5-6** in the QUICKSTART_ROADMAP.md to build the dashboard.

You'll have:
- Real-time metrics visualization
- Project lists with filtering
- Email activity feeds
- Natural language queries

---

## 🆘 Troubleshooting

### API won't start
```bash
# Check Python version
python3 --version  # Must be 3.11+

# Check if virtual environment is activated
which python  # Should show path in venv/

# Reinstall dependencies
pip install -r requirements.txt
```

### Database errors
```bash
# Check database path in .env
cat .env | grep DATABASE_PATH

# Verify file exists
ls -la ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db

# Check permissions
chmod 644 ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db
```

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
python3 backend/api/main.py --port 8001
```

---

## 📚 Additional Resources

- **Full Roadmap**: See QUICKSTART_ROADMAP.md for 12-week plan
- **API Docs**: http://localhost:8000/docs (when running)
- **n8n Docs**: https://docs.n8n.io/
- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/

---

## 💬 Questions?

Common questions:

**Q: Do I need to rewrite all my scripts?**
A: No! We're just wrapping them with an API. Your scripts work as-is.

**Q: Can I use PostgreSQL instead of SQLite?**
A: Yes! Just change DATABASE_URL in .env and install `psycopg2`.

**Q: How much will OpenAI cost?**
A: For your volume, probably $50-200/month. Start with gpt-3.5-turbo (cheaper).

**Q: Can I skip the dashboard?**
A: Yes, but the API + n8n are already super useful. Dashboard makes it visual.

---

**Ready? Run `./setup.sh` and let's go! 🚀**

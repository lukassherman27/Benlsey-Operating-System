# 🏗️ Bensley Intelligence Platform
**AI-Powered Operations System for Bensley Design Studios**

Transform from reactive coordination to proactive intelligence. Give Bill & Brian complete visibility, automate 35+ hours/week of admin work, and scale to 50+ projects without adding headcount.

---

## 🚀 QUICK START

```bash
# 1. Clone and setup (2 minutes)
./setup.sh

# 2. Configure your environment (2 minutes)
cp .env.example .env
nano .env  # Add your DATABASE_PATH and OPENAI_API_KEY

# 3. Start the API (instant)
source venv/bin/activate
python3 backend/api/main.py

# 4. Open in browser
open http://localhost:8000/docs
```

**That's it!** You now have a REST API serving all your project data.

---

## 📚 DOCUMENTATION

**New here? Start with one of these:**

1. **[BENSLEY_BRAIN_MASTER_PLAN.md](BENSLEY_BRAIN_MASTER_PLAN.md)** ⭐ **START HERE!** ⭐
   - Complete architecture with 4 phases
   - Current status (75% Phase 1 complete)
   - End goal vision
   - Progress tracking and timeline
   - **The single source of truth for what we're building**

2. **[GETTING_STARTED.md](GETTING_STARTED.md)** - 3-day hands-on guide
   - Get API running today
   - Build services tomorrow
   - Create first automation day 3

3. **[QUICKSTART_ROADMAP.md](QUICKSTART_ROADMAP.md)** - Complete 12-week plan
   - Week-by-week implementation guide
   - All code examples included
   - Success metrics defined

4. **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Detailed tracking
   - What's built vs not built
   - Action items prioritized
   - Technical decisions documented

---

## 💡 WHAT THIS DOES

### Current State (Your Scripts)
- ✅ Email processing with pattern learning
- ✅ Project management database
- ✅ RFI and proposal tracking
- ✅ Contact extraction
- ✅ Data quality tools

### What We're Adding
- 🚀 **REST API** - Access all data via endpoints
- 🤖 **AI Classification** - OpenAI-powered email intelligence
- ⚡ **Automation** - n8n workflows (daily digests, follow-ups)
- 📊 **Dashboard** - Real-time metrics for Bill & Brian
- 🧠 **Connection Engine** - Neo4j relationship intelligence

---

## 🎯 THE VISION

**Month 1**
- Daily intelligence briefings automated
- Email classification running
- API serving data to dashboard

**Month 3**
- Full dashboard operational
- 20% time savings achieved
- Team trained and using daily

**Month 6**
- 30%+ efficiency improvement
- 2-3 additional proposals won
- Complete operational autonomy

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────┐
│           Dashboard (Next.js)               │
│  Real-time metrics, queries, visualizations │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┴────────────────────────────┐
│         FastAPI Backend                     │
│  REST endpoints, WebSocket, authentication  │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┴────────────────────────────┐
│     Your Existing Intelligence              │
│  Email processor, pattern learner, etc.     │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┴────────────────────────────┐
│  Data Layer: SQLite → PostgreSQL + Neo4j    │
│  Projects, emails, patterns, relationships  │
└─────────────────────────────────────────────┘

         ⚡ n8n Automation ⚡
    (Daily digests, workflows, alerts)
```

---

## 📁 PROJECT STRUCTURE

```
backend/
├── api/           # FastAPI endpoints (✅ built)
├── core/          # Your existing scripts (⏳ move here)
├── services/      # Business logic (❌ to build)
└── models/        # Data models (❌ to build)

database/
├── schema.sql     # Current schema (⏳ export)
└── migrations/    # Version control (❌ to build)

automation/
└── n8n/           # Workflows (❌ to build)

frontend/
└── dashboard/     # Next.js app (❌ to build)

docs/              # Documentation (✅ complete)
```

---

## 🔧 TECH STACK

**Backend**
- FastAPI (Python 3.11+)
- SQLite → PostgreSQL
- Neo4j (graph relationships)
- Redis (caching)

**Frontend**
- Next.js 14
- TypeScript
- Tailwind CSS
- Recharts

**AI & Automation**
- OpenAI GPT-4
- n8n (workflow automation)

**DevOps**
- Docker + Docker Compose
- GitHub Actions (CI/CD)

---

## 💰 COSTS

**Monthly**: ~$100-300
- OpenAI API: $50-200
- Hosting: $50-100

**ROI**: $180k/year in time savings
- 35+ hours/week saved
- 2-3 more proposals won
- Break-even: Month 1

---

## ✅ CURRENT STATUS

**Phase 1 (Foundation): 75% Complete** 🎉
- ✅ 87 proposals imported and tracked
- ✅ 369 emails AI-processed with categorization
- ✅ 852 documents indexed with intelligent extraction
- ✅ Full-text search enabled (FTS5)
- ✅ 74 database indexes for performance
- ✅ Health monitoring with context-aware scoring
- 🔄 Email import (47/2,347 with full bodies)

**Next Up This Week:**
1. Complete email import (2,347 emails)
2. Build contact extraction
3. Build timeline builder
4. Complete Phase 1 (100%)

**See [BENSLEY_BRAIN_MASTER_PLAN.md](BENSLEY_BRAIN_MASTER_PLAN.md) for complete status & roadmap**

---

## 🆘 TROUBLESHOOTING

### API Won't Start
```bash
# Check Python version (need 3.11+)
python3 --version

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Database Not Found
```bash
# Check .env file
cat .env | grep DATABASE_PATH

# Verify file exists
ls -la ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db
```

**More help**: See [GETTING_STARTED.md](GETTING_STARTED.md) troubleshooting section

---

## 📞 RESOURCES

- **API Docs**: http://localhost:8000/docs (when running)
- **n8n Workflows**: http://localhost:5678 (after setup)
- **FastAPI Tutorial**: https://fastapi.tiangolo.com
- **n8n Docs**: https://docs.n8n.io

---

## 🎉 READY TO START?

```bash
# Run this now:
./setup.sh
```

Then open **[GETTING_STARTED.md](GETTING_STARTED.md)** and follow the 3-day guide.

You'll have a working API by end of day. 🚀

---

**Questions?** Check the docs folder or review existing scripts to see what you've already built!

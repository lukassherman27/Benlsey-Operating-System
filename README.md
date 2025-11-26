# Bensley Operations Platform

**AI-Powered Operations Dashboard for Bensley Design Studios**

Transform project management from reactive coordination to proactive intelligence. Complete visibility into proposals and active projects with automated data processing and real-time dashboards.

---

## ✅ WHAT'S WORKING NOW (November 2025)

### Live Applications
- **Backend API**: FastAPI with 100+ endpoints → http://localhost:8000
- **Frontend Dashboard**: Next.js proposal tracker → http://localhost:3002
- **API Documentation**: Interactive Swagger UI → http://localhost:8000/docs

### Core Features
- ✅ **Proposal Tracker Dashboard** - Full CRUD operations, status timeline, email intelligence
- ✅ **Email Processing** - AI-powered categorization and project matching
- ✅ **Document Intelligence** - PDF parsing with Claude API
- ✅ **Status Timeline** - Track proposal progression with historical changes
- ✅ **Quick Edit Dialog** - Update proposals inline with validation
- ✅ **Database Provenance** - Full audit trail on all data

### Data & Intelligence
- **Database**: SQLite with 56+ tables, 74 performance indexes
- **AI Integration**: Claude API for email/document processing
- **Proposals**: 87+ imported and tracked
- **Emails**: 369+ AI-processed with categorization
- **Documents**: 852+ indexed with intelligent extraction

---

## 🚀 QUICK START

```bash
# 1. Start Backend API (Terminal 1)
python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Start Frontend Dashboard (Terminal 2)
cd frontend
npm install  # First time only
npm run dev

# 3. Open in Browser
# Dashboard: http://localhost:3002
# API Docs:  http://localhost:8000/docs
```

**That's it!** You now have a fully functional operations dashboard.

---

## 📁 PROJECT STRUCTURE

```
bensley-operating-system/
├── frontend/              # Next.js 15 dashboard (✅ BUILT)
│   ├── src/app/(dashboard)/
│   │   ├── page.tsx          # Main dashboard
│   │   ├── tracker/          # Proposal tracker ✅
│   │   └── projects/         # Projects (in progress)
│   ├── src/components/
│   │   ├── dashboard/        # Dashboard widgets
│   │   ├── proposals/        # Proposal components
│   │   └── ui/              # shadcn/ui components
│   └── src/lib/
│       ├── api.ts           # API client
│       └── types.ts         # TypeScript definitions
│
├── backend/               # FastAPI backend (✅ BUILT)
│   ├── api/
│   │   └── main.py          # 100+ REST endpoints
│   ├── services/            # Business logic layer ✅
│   │   ├── proposal_tracker_service.py
│   │   ├── email_service.py
│   │   ├── financial_service.py
│   │   └── ... (15+ services)
│   └── database/
│       └── bensley_master.db  # SQLite database
│
├── database/
│   ├── bensley_master.db    # Main database (56+ tables)
│   └── migrations/          # 023 database migrations
│
├── scripts/              # Python utilities
│   ├── import_*.py         # Data import scripts
│   ├── parse_*.py          # Document parsers
│   └── *_processor.py      # Background processors
│
└── docs/                 # Documentation
    ├── guides/              # User/dev guides
    └── archive/             # Historical planning docs
```

---

## 🔧 TECH STACK

### Backend
- **API**: FastAPI (Python 3.11+)
- **Database**: SQLite → PostgreSQL (future)
- **AI**: Claude API (Anthropic)
- **Email**: IMAP integration

### Frontend
- **Framework**: Next.js 15.1.3 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **Data**: React Query (TanStack Query)
- **Charts**: Recharts

### Infrastructure
- **Development**: Local (Mac)
- **Production**: Mac Mini server (planned)
- **Version Control**: Git + GitHub

---

## 📊 CURRENT STATUS

**Phase 1: Dashboard Foundation (85% Complete)**

**Completed:**
- ✅ Backend API with full CRUD operations
- ✅ Proposal tracker dashboard (working)
- ✅ Email intelligence & categorization
- ✅ Status timeline tracking
- ✅ Quick edit functionality
- ✅ Database migrations system
- ✅ Provenance & audit tracking
- ✅ LLM training data export

**In Progress:**
- 🔄 Active Projects Dashboard
- 🔄 Financial metrics widgets
- 🔄 Cash flow forecasting
- 🔄 Invoice aging reports

**Next Sprint:**
- 📋 Complete financial dashboard
- 📋 RFI tracking interface
- 📋 Meeting notes integration
- 📋 Multi-user authentication

---

## 🎯 DEVELOPMENT GUIDE

### Running the System

```bash
# Check if servers are running
lsof -ti:8000  # Backend (should return PID)
lsof -ti:3002  # Frontend (should return PID)

# Start backend
python3 -m uvicorn backend.api.main:app --reload

# Start frontend (separate terminal)
cd frontend && npm run dev

# View logs
tail -f /tmp/bensley_api.log      # Backend logs
tail -f /tmp/frontend_dev.log     # Frontend logs
```

### Database Access

```bash
# Open database
sqlite3 database/bensley_master.db

# Useful queries
SELECT COUNT(*) FROM proposal_tracker;
SELECT * FROM proposal_status_history ORDER BY changed_at DESC LIMIT 10;
SELECT source_type, COUNT(*) FROM emails GROUP BY source_type;

# Run migrations
python3 database/migrate.py
```

### Making Changes

**Backend (Add new endpoint):**
1. Add route in `backend/api/main.py`
2. Add service method in `backend/services/`
3. Test with http://localhost:8000/docs

**Frontend (Add new component):**
1. Create component in `frontend/src/components/`
2. Add types to `frontend/src/lib/types.ts`
3. Add API call to `frontend/src/lib/api.ts`
4. Use in page component

---

## 📚 DOCUMENTATION

**For Developers:**
- [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) - Frontend development guide
- [CURRENT_STATUS.md](CURRENT_STATUS.md) - Real-time project status
- [.claude/PROJECT_CONTEXT.md](.claude/PROJECT_CONTEXT.md) - AI context & architecture

**For Planning:**
- [2_MONTH_MVP_PLAN.md](2_MONTH_MVP_PLAN.md) - 8-week implementation plan
- [COMPLETE_ARCHITECTURE_ASSESSMENT.md](COMPLETE_ARCHITECTURE_ASSESSMENT.md) - Full architecture analysis

**For Operations:**
- [PROPOSAL_TRACKER_GUIDE.md](PROPOSAL_TRACKER_GUIDE.md) - Using the proposal tracker
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment instructions

---

## 🆘 TROUBLESHOOTING

### Backend Won't Start

```bash
# Check Python version (need 3.11+)
python3 --version

# Check if port is in use
lsof -ti:8000 | xargs kill -9  # Kill existing process

# Check for errors
python3 -m uvicorn backend.api.main:app --reload
```

### Frontend Won't Build

```bash
# Clear cache and restart
cd frontend
rm -rf .next node_modules/.cache
npm install
npm run dev
```

### Database Issues

```bash
# Check database exists
ls -la database/bensley_master.db

# Verify tables
sqlite3 database/bensley_master.db ".tables"

# Check for corruption
sqlite3 database/bensley_master.db "PRAGMA integrity_check;"
```

### Dropdown Not Working (Fixed Nov 23, 2025)

If proposal edit dialogs don't accept input, ensure you have the latest code:
```bash
git pull origin main
# The useEffect fix in proposal-quick-edit-dialog.tsx resolves this
```

---

## 💰 COSTS & ROI

**Monthly Costs**: $100-200
- Claude API: $50-150
- Hosting (future): $50
- Total: ~$100-200/month

**ROI**: $180k/year in time savings
- 35+ hours/week saved on manual tracking
- 2-3 more proposals won per year
- Better cash flow visibility
- Break-even: Month 1

---

## 🎉 RECENT CHANGES

**November 23, 2025:**
- Fixed proposal tracker dropdown bug (useEffect pattern)
- Added conversation export for LLM training
- Updated .gitignore to exclude private training data
- Committed and pushed to GitHub

**November 22, 2025:**
- Implemented proposal tracker dashboard
- Added status timeline component
- Built email intelligence panel

**November 21, 2025:**
- Created proposal tracker service
- Added database migrations 018-023
- Integrated financial metrics APIs

---

## 🔗 KEY URLS

**Development:**
- Frontend: http://localhost:3002
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: `database/bensley_master.db`

**GitHub:**
- Repository: https://github.com/lukassherman27/Benlsey-Operating-System
- Current Branch: `claude/bensley-operations-platform-011CV3dp9CnqP1L5Rkjm6NYm`

---

## 📞 SUPPORT & RESOURCES

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Next.js Docs**: https://nextjs.org/docs
- **shadcn/ui**: https://ui.shadcn.com
- **React Query**: https://tanstack.com/query

---

## ✨ WHAT'S NEXT

**This Week:**
- Complete financial dashboard widgets
- Add invoice aging visualization
- Implement cash flow forecast

**Next Month:**
- Multi-user authentication
- Role-based access control
- Production deployment

**Phase 2 (Q1 2026):**
- Local LLM integration (Ollama)
- RAG/vector search
- Natural language queries

---

**Ready to contribute?** See [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) or [.claude/PROJECT_CONTEXT.md](.claude/PROJECT_CONTEXT.md) for development guidelines.

**Questions?** Check the `docs/` folder or review existing code patterns.

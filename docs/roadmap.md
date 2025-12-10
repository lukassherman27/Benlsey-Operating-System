# Roadmap

**Updated:** 2025-12-11
**Vision:** Bensley Brain - Everyone at Bensley has AI power

---

## 1. The Vision

```
TODAY: Lukas + Claude CLI → Only Lukas can use this

GOAL:  Everyone at Bensley has this power
       - Bill: "what's happening with Nusa Dua?" → gets answer
       - PM: "what RFIs are overdue?" → gets list
       - Model LEARNS from every interaction
```

**Core principle:** AI suggests → You approve → System learns

---

## 2. The Build Layers

```
LAYER 1: DATA INTAKE (Building Now)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Email channels: lukas@, projects@, invoices@, dailywork@, scheduling@
Voice: Meeting recorder → OneDrive → transcribe → summarize
Each source categorized and stored

LAYER 2: LINKING & CONTEXT (Next)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Contact → Project mappings
Meeting transcripts → Projects
Invoices → Projects
Everything connected to the right project

LAYER 3: INTELLIGENCE (Future)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task extraction from emails
Deliverable tracking
Timeline/deadline monitoring
Action items
Project health scores

LAYER 4: BENSLEY BRAIN (End Goal)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full picture per project:
- All correspondence history
- All meetings + summaries
- All invoices + payment status
- All deliverables + deadlines
- Who's working on what
- Where are we in the timeline
```

---

## 3. December 2025 - COMPLETED

### ✅ Email Sync Automation
- Cron runs hourly
- Multi-account ready (just add creds to .env)

### ✅ Data Quality Cleanup (Dec 8-10)
- Date formats normalized (all ISO now)
- Attachment→Proposal linking (40% linked)
- Contact names fixed (0 missing)
- last_contact_date accuracy (100%)
- Duplicate email links removed (266)

### ✅ Batch Suggestion System
- Working: 48 batches approved
- 341 learned patterns
- Confidence tiers implemented

### ✅ Fixed by Builder Agent (Dec 10)
- Frontend build now works
- /api/proposals/stats returns real numbers (57 proposals, 16 active projects)

---

## 4. January 2026 Plan

### Week 1 (Jan 6-10): Fix & Stabilize
```
[✅] Builder Agent: Fix frontend build (DONE Dec 10)
[✅] Builder Agent: Fix /api/proposals/stats (DONE Dec 10)
[✅] Process 12 pending suggestions (DONE Dec 10)
[✅] Email Review Queue: /api/emails/review-queue (DONE Dec 11)
[✅] Sent Email Linking + Proposal Version Tracking (DONE Dec 11)
[ ] Verify dashboard displays real data
```

### Week 2 (Jan 13-17): Connect projects@bensley.com
```
[ ] Get credentials from IT
[ ] Add to EMAIL_ACCOUNTS in .env
[ ] Run initial sync (expect 2,000+ emails)
[ ] Review batch suggestions, approve links
[ ] Create patterns for new senders
```

### Week 3 (Jan 20-24): Meeting Recorder MVP
```
[ ] Simple web form: title, project, attendees
[ ] Audio upload to OneDrive shared folder
[ ] Whisper transcription (manual trigger)
[ ] GPT summary generation
[ ] Link transcript → project
```

### Week 4 (Jan 27-31): Bill's First Query
```
[ ] Slack bot OR simple web page
[ ] Bill asks: "What's the status of [project]?"
[ ] System returns: last emails, contacts, status
[ ] Start with READ-ONLY access
```

### January Success Metrics
| Metric | Target |
|--------|--------|
| Email inboxes synced | 2 (lukas + projects) |
| Dashboard working | Yes |
| Meeting transcripts | 10+ |
| Bill can query | Yes (read-only) |

---

## 5. Q1 2026 Goals

| Goal | Target | Status |
|------|--------|--------|
| Email inboxes | 4+ (lukas, projects, bill, invoices) | - |
| Meeting transcripts linked | 50+ | - |
| Bill queries per week | 5+ | - |
| Weekly reports automated | Yes | - |
| All proposals enriched | 100% | - |

---

## 6. What's Connected vs NOT

### Connected ✅
| Source | Records | Status |
|--------|---------|--------|
| lukas@bensley.com | 3,727 emails | Automated (cron hourly) |
| Voice Memos (your Mac) | 39 transcripts | Manual |

### NOT Connected ❌
| Source | Priority | When |
|--------|----------|------|
| projects@bensley.com | High | Jan Week 2 |
| bill@bensley.com | Medium | Jan Week 4 |
| invoices@bensley.com | Medium | Feb 2026 |
| dailywork@bensley.com | Low | Q1 2026 |
| scheduling@bensley.com | Low | Q1 2026 |
| Shared OneDrive (meetings) | Medium | Jan Week 3 |

---

## 7. Phase Timeline

| Phase | When | Focus |
|-------|------|-------|
| **Foundation** | Dec 2025 | Email sync, meeting recorder, learning loop |
| **2C** | Jan 2026 | ESCAPISM 3: Creative content |
| **2.5** | Feb 2026 | Reports & polish |
| **3.0** | Mar 2026 | RAG, Vector store, MCP |
| **4.0** | Q2 2026 | Contract/proposal automation |
| **5.0** | Q4 2026 | Local LLM |
| **6.0** | 2027 | Bensley Model (fully local) |

---

## 6. Agent Structure

```
YOU (Lukas)
    ↓
COORDINATOR AGENT (only one who updates SSOT)
├── Develops tasks and roadmap
├── Updates STATUS.md, HANDOFF.md, roadmap.md, ARCHITECTURE.md
├── Routes work to specialist agents
├── Receives summaries from all agents
└── Makes final decisions on approach

SPECIALIST AGENTS (do work, report back)
├── EMAIL AGENT - Sync, categorize, link emails
├── SUGGESTION AGENT - Learning loop, patterns, training
├── MEETING AGENT - Transcription, summaries
├── ENRICHMENT AGENT - Fill in proposals/projects
└── BUILDER AGENT - Code, UI, infrastructure
```

### Agent Rules
1. **ONLY Coordinator updates SSOT files** (STATUS, HANDOFF, roadmap, ARCHITECTURE)
2. Specialist agents do their work and produce summaries
3. You relay summaries to Coordinator
4. Coordinator synthesizes and updates docs
5. This prevents conflicting edits and maintains coherence

---

## 7. Future Phases

### Phase 2C: ESCAPISM 3 (Jan 2026)
- Bill's interviews (PDFs, videos)
- ESCAPISM 1 & 2 books
- Instagram posts + analytics
- New tables: `bill_quotes`, `interviews`, `social_media_posts`

### Phase 3.0: RAG + MCP (Mar 2026)
- Database encryption (SQLCipher)
- Vector store (Chroma)
- MCP Server (Claude queries DB directly)
- Cross-linking via semantic search

### Phase 5.0: Local AI (2026-2027)
- Local embeddings (stop sending to OpenAI)
- Local LLM (Ollama) for simple tasks
- Distillation (train on GPT outputs)
- Bensley Model (fully local)

---

## 8. Success Metrics

### By End of January 2026
| Metric | Target |
|--------|--------|
| Email inboxes synced | 4+ |
| Team can record meetings | Yes |
| Suggestion learning working | Yes |

### By End of Q1 2026
| Metric | Target |
|--------|--------|
| Bill quotes ingested | 500+ |
| Weekly reports | Automated |
| All proposals enriched | 99/99 |

---

## 9. Agent Rules

1. **Never auto-link** - Always create suggestions
2. **Always name projects** - "25 BK-033 (Ritz-Carlton Reserve Nusa Dua)"
3. **Test before done** - Run code, verify it works
4. **Update docs** - Next agent needs to know
5. **Commit and push** - Always push to GitHub
6. **Don't create random files** - Use existing structure

---

## 10. Folder Structure (ENFORCED)

```
Benlsey-Operating-System/
├── .claude/              # STATUS.md, HANDOFF.md, commands/
├── docs/                 # ONLY: roadmap.md, ARCHITECTURE.md
├── backend/              # FastAPI app
│   ├── api/routers/      # 28 API routers
│   └── services/         # 60+ services + suggestion_handlers/
├── frontend/             # Next.js app
├── database/             # bensley_master.db, migrations/
├── scripts/core/         # Active CLI scripts ONLY
├── voice_transcriber/    # Transcription
├── exports/              # CSV/data exports
├── training/             # Model training data
├── reports/              # Generated reports
└── CLAUDE.md             # Entry point for agents
```

**RULES FOR NEW AGENTS:**
1. **NEVER create files at root level** - Use existing folders
2. **NEVER create new docs/** - Update existing SSOT files
3. **Scripts go in scripts/core/** - Not scripts/ root
4. **Services go in backend/services/** - Not backend/ root
5. **No new TODO.md, PLAN.md, etc.** - Use roadmap.md

**If you must create a file, ASK FIRST.**

---

## 11. Quick Commands

```bash
# Run servers
cd backend && uvicorn api.main:app --reload --port 8000
cd frontend && npm run dev

# Sync emails
python scripts/core/scheduled_email_sync.py

# Check state
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM emails;"
```

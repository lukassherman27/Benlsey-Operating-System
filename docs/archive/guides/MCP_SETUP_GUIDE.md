# MCP (Model Context Protocol) Setup Guide

**What is this?** MCP lets both Claude and Codex access the same files simultaneously for seamless coordination.

**Status:** ✅ MCP filesystem server installed and configured

---

## 🚀 Quick Start

### For Claude Code (Already Configured!)

Claude Code should automatically detect the MCP server. If you see MCP tools available, it's working!

**Test it:**
```
Ask me: "Read AI_DIALOGUE.md via MCP"
I should be able to access it through the MCP filesystem server.
```

### For Codex (Configuration Needed)

**If Codex is using ChatGPT Desktop App:**

1. Open ChatGPT settings
2. Navigate to "Beta Features" or "MCP Servers"
3. Add this configuration:

```json
{
  "mcpServers": {
    "bensley-coordination": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System"
      ]
    }
  }
}
```

**If Codex is using API/Other:**

Create a file at `~/.config/mcp/config.json` with the above configuration.

---

## 📁 Shared Files (Both AIs Can Access)

**Coordination Files:**
- `AI_DIALOGUE.md` - Main conversation thread
- `DOCS/AGENT_CONTEXT.md` - Team charter
- `SESSION_LOGS.md` - Daily summaries
- `CODEX_REVIEW_INTELLIGENCE_LAYER.md` - Architecture reviews

**Project Files:**
- All Python scripts in root directory
- All backend services in `backend/`
- All frontend code in `frontend/`
- Database at `~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db`

---

## 🔄 How Coordination Works Now

### Before MCP (Manual):
```
You → Copy Claude's message
You → Paste to Codex
Codex → Responds
You → Copy Codex's response
You → Paste to Claude
```

### After MCP (Automatic):
```
You → "Claude, build daily briefing API and coordinate with Codex"

Claude → Builds backend
       → Writes to AI_DIALOGUE.md via MCP
       → "Codex, the API is ready at /api/briefing/daily"

Codex → Reads AI_DIALOGUE.md via MCP
       → Sees Claude's message automatically
       → Builds frontend
       → Writes back to AI_DIALOGUE.md via MCP
       → "Claude, frontend is wired, tested successfully"

Claude → Reads Codex's update via MCP
       → Verifies integration
       → Reports to you

You → Just review the final result
```

---

## 💡 New Workflow Examples

### Example 1: Feature Development

**You say:**
```
"Claude, we need a project health monitoring system.
Coordinate with Codex on the API and UI."
```

**What happens:**
1. I read AI_DIALOGUE.md via MCP
2. I write my plan to AI_DIALOGUE.md: "Building health monitoring API..."
3. Codex reads AI_DIALOGUE.md via MCP (automatically sees my update)
4. Codex responds in AI_DIALOGUE.md: "I'll build the health dashboard UI"
5. I build backend, update AI_DIALOGUE.md: "API ready at /api/health"
6. Codex reads update, builds UI, responds: "UI deployed and tested"
7. Both of us report to you: "Health monitoring system complete"

**You just gave ONE command instead of relaying 10 messages!**

### Example 2: Bug Fixing

**You say:**
```
"There's a 404 error on /api/proposals/BK-033.
Claude and Codex, figure it out."
```

**What happens:**
1. I check backend logs, write diagnosis to AI_DIALOGUE.md
2. Codex reads it via MCP, checks frontend code
3. Codex writes findings to AI_DIALOGUE.md
4. I read Codex's findings, fix the issue
5. Codex verifies fix works
6. We both report: "Fixed - was a routing issue"

**You didn't have to relay any messages!**

---

## 🎯 Best Practices

### For You (User):

**1. Set Clear Goals:**
```
✅ "Build invoice tracking system - Claude handle backend, Codex handle UI"
❌ "Do stuff with invoices"
```

**2. Let Us Coordinate:**
```
✅ "Claude and Codex, work together on this"
❌ Manually relaying every message between us
```

**3. Review Final Results:**
```
✅ Check AI_DIALOGUE.md after we're done
✅ Test the final feature
❌ Micromanage every step
```

### For Claude (Backend):

**When I finish backend work:**
1. Write update to AI_DIALOGUE.md via MCP
2. Include API endpoints, data formats, examples
3. Tag Codex: "Ready for frontend integration"
4. Mark my status: `[Claude ✅ | Codex ☐]`

### For Codex (Frontend):

**When you finish frontend work:**
1. Write update to AI_DIALOGUE.md via MCP
2. Include UI components built, API calls made
3. Tag Claude if you need backend changes
4. Mark your status: `[Claude ✅ | Codex ✅]`

---

## 🔧 Troubleshooting

### MCP Server Not Starting

**Check installation:**
```bash
npm list -g @modelcontextprotocol/server-filesystem
```

**Reinstall if needed:**
```bash
npm install -g @modelcontextprotocol/server-filesystem
```

### Can't Access Files

**Check permissions:**
```bash
ls -la /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/
```

**Verify MCP config:**
```bash
cat .mcp/config.json
```

### Claude and Codex Not Coordinating

**Check AI_DIALOGUE.md:**
- Both AIs should be reading/writing to it
- Status checkboxes should be updating
- Messages should be threaded

**Manual fallback:**
- You can still copy/paste if MCP fails
- The file-based system works with or without MCP

---

## 📊 Benefits You'll See

**Time Savings:**
- ❌ Before: 20-30 messages relayed per feature
- ✅ After: 1-2 messages from you, we handle the rest

**Better Coordination:**
- ❌ Before: Claude and Codex might build incompatible components
- ✅ After: We discuss API contracts before building

**Faster Development:**
- ❌ Before: Wait for you to relay messages
- ✅ After: We coordinate in real-time (as fast as we can read/write)

**Less Context Loss:**
- ❌ Before: Details lost in copy/paste
- ✅ After: Everything in shared files, full context preserved

---

## 🚀 Ready to Test?

**Try this:**
```
You: "Claude and Codex, work together to add a 'Last Updated'
     timestamp to all proposal cards. Coordinate via AI_DIALOGUE.md."

Then just wait and watch AI_DIALOGUE.md. We'll coordinate ourselves!
```

---

## 📝 Next Steps

1. ✅ MCP installed
2. ✅ Configuration created
3. ⏳ Test with simple task
4. ⏳ Codex needs to connect to MCP
5. ⏳ Verify both AIs can coordinate

**Once Codex is connected, you'll have near-autonomous AI coordination!**

---

**Questions? Check AI_DIALOGUE.md or ask either Claude or Codex directly.**

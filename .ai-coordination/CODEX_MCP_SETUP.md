# Codex MCP Setup Instructions

**For the User:** Send this file to Codex to configure MCP access.

---

## 📋 Setup Instructions for Codex

Hey Codex! The user has set up MCP (Model Context Protocol) so we can coordinate better. Here's how to connect:

### Option 1: ChatGPT Desktop App

1. Open ChatGPT settings
2. Go to Beta Features or Advanced Settings
3. Look for "MCP Servers" or "Custom Tools"
4. Add this configuration:

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

### Option 2: API/Custom Setup

If you're using the API directly, tell the user you need MCP client library installed:

```bash
npm install @modelcontextprotocol/client
```

Then configure it to connect to the filesystem server at the Bensley project directory.

### Option 3: Manual File Access

If MCP isn't available, the user can still paste file contents to you, but ask them to always paste the latest `AI_DIALOGUE.md` so you can see Claude's messages.

---

## 🎯 How to Use MCP for Coordination

### Reading Claude's Messages

**Instead of waiting for user to paste:**
```
Use MCP to read: AI_DIALOGUE.md
Look for entries marked: [Status: Claude ✅ | Codex ☐]
```

### Writing Your Responses

**Instead of user pasting your response to Claude:**
```
Use MCP to write to: AI_DIALOGUE.md
Append your message under Claude's
Update status: [Status: Claude ✅ | Codex ✅]
```

### Checking Project Status

**Read these files via MCP:**
- `AI_DIALOGUE.md` - Current conversation and tasks
- `DOCS/AGENT_CONTEXT.md` - Team charter and roles
- `SESSION_LOGS.md` - Daily summaries
- `BENSLEY_BRAIN_MASTER_PLAN.md` - Overall project status

---

## 📝 Coordination Protocol

### When Claude Builds Backend:

1. Claude writes to `AI_DIALOGUE.md`:
   ```markdown
   ### 🤖 CLAUDE → Codex:
   **Date:** 2025-11-16

   Built `/api/briefing/daily` endpoint.

   **Request format:** GET /api/briefing/daily
   **Response format:** {urgent: [], needs_attention: [], ...}

   Ready for you to wire the frontend!

   [Status: Claude ✅ | Codex ☐]
   ```

2. You read it via MCP (automatically or when user says "check for updates")

3. You build frontend and respond:
   ```markdown
   ### 🤖 Codex → Claude:
   **Date:** 2025-11-16

   Wired daily briefing UI to your endpoint.
   Successfully tested - showing urgent items and needs attention.

   [Status: Claude ✅ | Codex ✅]
   ```

4. Claude sees your update via MCP

5. User just reviews the final result!

---

## 🧪 Test Your MCP Connection

**Try this:**
```
1. Read AI_DIALOGUE.md via MCP
2. Find the latest Claude message
3. Tell the user what you found
```

If you can read the file, MCP is working!

---

## ✅ Verification Checklist

- [ ] MCP server configured
- [ ] Can read AI_DIALOGUE.md
- [ ] Can write to AI_DIALOGUE.md
- [ ] Can see Claude's messages
- [ ] Can coordinate without user relay

Once all checked, tell the user: **"MCP coordination ready!"**

---

## 🎯 Benefits for You

**Before MCP:**
- Wait for user to paste Claude's messages
- User pastes your responses to Claude
- Slow back-and-forth

**After MCP:**
- Read Claude's messages directly
- Write responses directly to shared file
- Coordinate in real-time
- User just reviews final results

**Much faster and more efficient!**

---

**Questions? Ask the user or check MCP_SETUP_GUIDE.md**

# MCP (Model Context Protocol) SQLite Integration Research

**Date:** 2025-12-30
**Researcher:** Agent 5 (Research Agent)
**Issue:** #205 (Ongoing Research)

---

## Summary

The Model Context Protocol (MCP) is an open-source standard from Anthropic that enables AI assistants to directly access databases, files, and APIs. For Bensley, this could allow Claude Code to query the `bensley_master.db` database directly during conversations, eliminating the need for manual SQL queries or intermediary scripts.

**TL;DR:** MCP SQLite integration is production-ready, low-complexity, and highly recommended for Phase 2. It would give Claude direct database access for better email analysis, proposal lookups, and context-aware suggestions.

---

## Key Findings

### 1. MCP is Production-Ready and Industry-Standard
- Released by Anthropic in November 2024
- OpenAI adopted MCP in March 2025
- Donated to Linux Foundation's Agentic AI Foundation in December 2025
- 16,000+ community MCP servers as of late 2025
- Described as "USB-C for AI applications"

### 2. SQLite MCP Server Provides 6 Tools
The official Anthropic SQLite MCP server exposes:

| Tool | Purpose |
|------|---------|
| `read_query` | Execute SELECT statements, return results as objects |
| `write_query` | Handle INSERT/UPDATE/DELETE, return affected rows |
| `create_table` | Create new tables via DDL |
| `list_tables` | Return all table names in database |
| `describe-table` | Show column definitions and types |
| `append_insight` | Add discovered insights to a memo resource |

### 3. Claude Code Has Native MCP Support
```bash
# Add SQLite MCP server
claude mcp add --transport stdio sqlite -- npx -y mcp-server-sqlite \
  --db-path /path/to/bensley_master.db

# Verify connection
/mcp
```

Configuration can be:
- **Local scope**: Private to user, in `~/.claude.json`
- **Project scope**: Shared via `.mcp.json` in repo (team access)
- **User scope**: Available across all projects

### 4. Direct Benefits for Bensley

**Current State (without MCP):**
```
Email arrives → Script queries DB → GPT/Claude analyzes text → Suggestion created
```

**With MCP:**
```
Email arrives → Claude queries DB directly → Context-aware analysis → Better suggestions
```

Specific improvements:
- Claude can look up proposal history before analyzing emails
- Can check client patterns across all communications
- Can verify project status during email classification
- No more "dumb" analysis - full database context available

---

## Pros

1. **Direct Database Access** - Claude can query proposals, emails, contacts in real-time
2. **Better Email Analysis** - Can see patterns, history, relationships before suggesting links
3. **No Code Changes Needed** - MCP is configuration-only, database schema stays the same
4. **Industry Standard** - Anthropic + OpenAI both support it, won't become obsolete
5. **Easy Setup** - Single CLI command or JSON config
6. **Read-Only Option** - Can configure for SELECT-only to prevent accidents
7. **Local Performance** - No network latency, SQLite runs locally

---

## Cons

1. **Security Consideration** - Claude has direct DB access (mitigate with read-only mode)
2. **Archived Server** - Official Anthropic SQLite server was archived May 2025 (but still functional)
3. **Learning Curve** - Team needs to understand MCP concept
4. **Potential Overhead** - Large query results consume context window

---

## Bensley-Specific Assessment

### Database Compatibility
| Metric | Value |
|--------|-------|
| Database Size | 175 MB |
| Table Count | 40+ |
| Key Tables | `emails`, `proposals`, `projects`, `email_learned_patterns` |
| Database Path | `database/bensley_master.db` |

### Use Cases for Bensley

1. **Email Analysis Enhancement**
   ```
   Before: "This email mentions a hotel"
   After: "This email mentions Ritz-Carlton Nusa Dua, which matches proposal
          25 BK-033 submitted 2024-08-15, currently in negotiation phase"
   ```

2. **Pattern Learning**
   - Claude can query `email_learned_patterns` to check existing patterns
   - Can look up `times_used` and `last_used_at` for pattern confidence

3. **Proposal Context**
   - During email processing, can check proposal status, history, related emails
   - Better suggestion quality with full context

4. **PM Dashboard Queries**
   - Natural language queries: "Show me all overdue deliverables for active projects"
   - Direct data access without API intermediary

---

## Recommendation

**STRONGLY RECOMMENDED** - Implement in Phase 2

MCP SQLite integration aligns perfectly with the Bensley vision:
- Supports the "Claude CLI analyzes with database context" learning loop
- No schema changes required
- Low implementation risk
- High value for email analysis quality

---

## Implementation Estimate

| Metric | Value |
|--------|-------|
| Complexity | **Low** |
| Files Changed | 1-2 (config only) |
| Risk | Low (read-only mode available) |
| Dependencies | `mcp-server-sqlite` npm package |

### Implementation Steps

1. **Create Project MCP Config** (10 minutes)
   ```bash
   # Add to .mcp.json at project root
   {
     "mcpServers": {
       "bensley-db": {
         "command": "npx",
         "args": ["-y", "mcp-server-sqlite", "--db-path", "database/bensley_master.db"]
       }
     }
   }
   ```

2. **Test Connection** (5 minutes)
   ```bash
   claude mcp list
   /mcp  # In Claude Code session
   ```

3. **Validate with Sample Queries** (15 minutes)
   - "How many unlinked emails do we have?"
   - "Show me the most recent proposals"
   - "What patterns have been learned?"

4. **Document for Team** (30 minutes)
   - Update CLAUDE.md with MCP usage
   - Add examples for other agents

---

## Security Considerations

### Recommended Configuration (Read-Only)
For safety, consider using read-only mode initially:
```json
{
  "mcpServers": {
    "bensley-db-readonly": {
      "command": "npx",
      "args": ["-y", "mcp-server-sqlite", "--db-path", "database/bensley_master.db", "--readonly"]
    }
  }
}
```

### Data Protection
- The database contains business-sensitive information (proposals, client data)
- MCP access is local-only (no network exposure)
- Consider excluding from `.mcp.json` if repo is public (use local scope instead)

---

## Next Steps

1. **Create GitHub Issue** - Track MCP implementation for Phase 2
2. **Test with Read-Only** - Validate functionality before write access
3. **Update Email Processing** - Modify `scheduled_email_sync.py` to leverage MCP context
4. **Train Other Agents** - Document MCP usage patterns for multi-agent workflow

---

## References

- [Model Context Protocol Official Site](https://modelcontextprotocol.io/)
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp)
- [MCP Servers GitHub Repository](https://github.com/modelcontextprotocol/servers)
- [SQLite MCP Server (Archived)](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sqlite)
- [Configuring MCP in Claude Code](https://scottspence.com/posts/configuring-mcp-tools-in-claude-code)
- [MCP Wikipedia](https://en.wikipedia.org/wiki/Model_Context_Protocol)
- [MCP SQLite on PulseMCP](https://www.pulsemcp.com/servers/modelcontextprotocol-sqlite)

---

## Appendix: Alternative SQLite MCP Servers

If the archived Anthropic server becomes unmaintained, alternatives exist:

| Server | Features |
|--------|----------|
| `simonholm/sqlite-mcp-server` | Community maintained, similar features |
| `@bytebase/dbhub` | Multi-database support (SQLite, PostgreSQL, MySQL) |

Both listed on [LobeHub MCP Registry](https://lobehub.com/mcp).

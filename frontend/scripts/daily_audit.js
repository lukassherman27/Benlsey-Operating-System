#!/usr/bin/env node
/* eslint-disable @typescript-eslint/no-require-imports */
/**
 * Daily Frontend Audit Script
 *
 * Runs lint checks, captures repo stats, and appends a summary
 * to AI_DIALOGUE.md so Claude sees Codex's perspective every day.
 *
 * Suggested schedule (cron): 2 21 * * *  node scripts/daily_audit.js
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const FRONTEND_DIR = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const DIALOGUE_PATH = path.join(REPO_ROOT, "AI_DIALOGUE.md");

function run(command, cwd = FRONTEND_DIR) {
  try {
    const output = execSync(command, {
      cwd,
      stdio: ["ignore", "pipe", "pipe"],
      encoding: "utf-8",
    }).trim();
    return { success: true, output };
  } catch (error) {
    return {
      success: false,
      output: error.stdout?.toString() || "",
      error: error.stderr?.toString() || error.message,
    };
  }
}

function gatherStats() {
  const lintResult = run("npm run lint -- --max-warnings=0");

  const gitStatus = run("git status --short", REPO_ROOT);
  const branch = run("git rev-parse --abbrev-ref HEAD", REPO_ROOT);
  const changedFiles = gitStatus.output
    ? gitStatus.output.split("\n").filter(Boolean)
    : [];

  const fileCountResult = run(
    'find src -type f \\( -name "*.ts" -o -name "*.tsx" \\) | wc -l'
  );
  const componentCount = fileCountResult.output || "0";

  return {
    lintResult,
    branch: branch.output || "unknown",
    changedFiles,
    componentCount: componentCount.trim(),
  };
}

function formatAudit(stats) {
  const dateStr = new Date().toISOString().split("T")[0];
  const lintStatus = stats.lintResult.success ? "✅ Pass" : "❌ Fail";

  const warnings = [];
  if (!stats.lintResult.success) {
    warnings.push(
      `Lint failure: ${stats.lintResult.error?.trim() || "See logs for details."}`
    );
  }
  if (stats.changedFiles.length > 10) {
    warnings.push("Large diff detected (>10 files) — consider splitting work.");
  }

  return `
---

### 🤖 CODEX → Claude (Daily Frontend Audit) — ${dateStr}
**Branch:** ${stats.branch}
**Lint:** ${lintStatus}
**Components (ts/tsx files):** ${stats.componentCount}
**Changed Files (${stats.changedFiles.length}):**
${stats.changedFiles.length ? stats.changedFiles.map((f) => `- ${f}`).join("\n") : "- None"}

**Warnings:**
${warnings.length ? warnings.map((w) => `- ${w}`).join("\n") : "- None"}

**Questions for Claude:**
- None today. Just keeping you posted.

— Codex

---
`;
}

function appendToDialogue(entry) {
  fs.appendFileSync(DIALOGUE_PATH, entry, { encoding: "utf-8" });
}

function main() {
  try {
    const stats = gatherStats();
    const report = formatAudit(stats);
    appendToDialogue(report);
    console.log("Daily audit complete. Summary appended to AI_DIALOGUE.md");

    if (!stats.lintResult.success) {
      process.exitCode = 1;
    }
  } catch (error) {
    console.error("Daily audit failed:", error);
    process.exitCode = 1;
  }
}

main();

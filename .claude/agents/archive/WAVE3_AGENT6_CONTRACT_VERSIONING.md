# 📑 Agent 6: Contract Versioning & Negotiation Tracking

**Wave:** 3 (Advanced)
**Priority:** MEDIUM - Future scalability
**Status:** AWAITING AUDIT

---

## ⚠️ MANDATORY PROTOCOL

1. ✅ **READ** `.claude/MASTER_ARCHITECTURE.md`
2. ✅ **READ** `.claude/ALIGNMENT_AUDIT.md`
3. 🔍 **AUDIT** your assigned area
4. 📊 **REPORT** findings (create `AGENT6_AUDIT_REPORT.md`)
5. ⏸️ **WAIT** for user approval
6. ✅ **EXECUTE** only after approval
7. 📝 **DOCUMENT** changes

---

## 🎯 YOUR MISSION

Build contract versioning and negotiation tracking system:
- Track multiple contract versions (v1, v2, v3, etc.)
- Detect what changed between versions
- Track negotiation history (who changed what, when)
- Link contract changes to email threads
- Visual diff viewer for contracts
- Audit trail for legal compliance

**User Context:** "Contracts go through multiple rounds of negotiation. Need to track: What changed? Who requested it? What email thread? Which version did we sign?"

---

## 🔍 PHASE 1: AUDIT

### Your Audit Checklist:

**1. Contract Storage Verification**
```bash
# Check contract_metadata table
sqlite3 database/bensley_master.db ".schema contract_metadata"

# Check for version tracking
sqlite3 database/bensley_master.db "SELECT contract_id, version, signed_date FROM contract_metadata LIMIT 10"

# Check contract document storage
sqlite3 database/bensley_master.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%contract%'"
```

**Report:**
- [ ] Does `contract_metadata` table support versioning?
- [ ] Is there a `contract_versions` table?
- [ ] How are contract PDFs currently stored?
- [ ] Is there version numbering (v1, v2, etc.)?

**2. Contract Change Detection**
```bash
# Check if contract text is extracted
sqlite3 database/bensley_master.db "SELECT contract_id, contract_text FROM contract_metadata WHERE contract_text IS NOT NULL LIMIT 3"

# Check parsing scripts
ls -lh *contract*.py | grep -i parse
```

**Report:**
- [ ] Is contract text extracted from PDFs?
- [ ] What parsing scripts exist?
- [ ] Can we compare text between versions?
- [ ] Is OCR needed for scanned contracts?

**3. Email-Contract Linkage**
```bash
# Check email_contract_links or similar
sqlite3 database/bensley_master.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%email%contract%'"

# Check email attachments
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_attachments WHERE attachment_name LIKE '%contract%' OR attachment_name LIKE '%.pdf'"
```

**Report:**
- [ ] Can we link emails to specific contract versions?
- [ ] Are contract PDFs tracked as email attachments?
- [ ] Is there an email-contract linking table?

**4. Negotiation History Infrastructure**
```bash
# Check for audit/history tables
sqlite3 database/bensley_master.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%history%' OR name LIKE '%audit%'"

# Check contract_audit_log or similar
sqlite3 database/bensley_master.db ".schema contract_audit_log"
```

**Report:**
- [ ] Does `contract_audit_log` table exist?
- [ ] What history tracking exists?
- [ ] Can we capture who/what/when for changes?

**5. Backend API Audit**
```bash
# Check for contract endpoints
grep -n "contract" backend/api/main.py | grep "def"

# Check version-related endpoints
grep -A 20 "contract.*version" backend/api/main.py
```

**Report:**
- [ ] What contract endpoints exist?
- [ ] Are there version-specific endpoints?
- [ ] What's missing?

---

## 📊 PHASE 2: REPORT

Create `AGENT6_AUDIT_REPORT.md` with:

**Findings:**
- Contract storage infrastructure assessment
- Version tracking capabilities
- Change detection feasibility
- Email-contract linkage status

**Proposed Solution:**
- Version numbering scheme (semantic? sequential?)
- Change detection algorithm (text diff? clause comparison?)
- Negotiation history capture method
- Frontend diff viewer approach

**Architecture Alignment:**
- Uses existing `contract_metadata`? YES/NO
- Creates `contract_versions` table? YES/NO
- Integrates with email system? HOW
- Conflicts with other agents? NONE/[DESCRIBE]

**Questions for User:**
1. Are contract PDFs stored locally or in cloud? Where?
2. Do you want automatic version detection or manual tagging?
3. What level of change tracking? (clause-level? paragraph? whole document?)
4. Should system alert when significant contract terms change?

---

## ⏸️ PHASE 3: AWAIT APPROVAL

---

## ✅ PHASE 4: EXECUTION

### Task 1: Contract Versioning Schema

**Migration:** `database/migrations/040_contract_versioning.sql`
```sql
-- Contract versions table
CREATE TABLE IF NOT EXISTS contract_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    version_number TEXT NOT NULL, -- "v1", "v2", "v3", etc.
    version_date DATE,
    contract_pdf_path TEXT,
    contract_text TEXT,
    extracted_clauses TEXT, -- JSON
    is_signed BOOLEAN DEFAULT 0,
    signed_by TEXT,
    signed_date DATE,
    notes TEXT,
    uploaded_by TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contract_metadata(contract_id)
);

-- Contract change history
CREATE TABLE IF NOT EXISTS contract_change_history (
    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    from_version_id INTEGER,
    to_version_id INTEGER NOT NULL,
    change_type TEXT, -- "clause_added", "clause_modified", "clause_removed", "term_changed"
    section_name TEXT,
    old_text TEXT,
    new_text TEXT,
    changed_by TEXT,
    change_reason TEXT,
    email_id INTEGER, -- Link to email that requested change
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contract_metadata(contract_id),
    FOREIGN KEY (from_version_id) REFERENCES contract_versions(version_id),
    FOREIGN KEY (to_version_id) REFERENCES contract_versions(version_id),
    FOREIGN KEY (email_id) REFERENCES emails(email_id)
);

CREATE INDEX IF NOT EXISTS idx_contract_versions_contract ON contract_versions(contract_id);
CREATE INDEX IF NOT EXISTS idx_contract_changes_contract ON contract_change_history(contract_id);
```

### Task 2: Contract Version Detector

**File:** `contract_version_detector.py` (new file)
```python
#!/usr/bin/env python3
"""
Contract Version Detection and Comparison
"""
import database_config
import difflib
import re
from datetime import datetime

class ContractVersionDetector:
    def __init__(self):
        self.conn = database_config.get_db_connection()
        self.cursor = self.conn.cursor()

    def add_version(self, contract_id: int, pdf_path: str, version_number: str = None):
        """
        Add new contract version
        Auto-increment version if not specified
        """
        # Get latest version number
        if not version_number:
            self.cursor.execute("""
                SELECT version_number FROM contract_versions
                WHERE contract_id = ?
                ORDER BY version_id DESC LIMIT 1
            """, (contract_id,))

            last_version = self.cursor.fetchone()
            if last_version:
                # Extract number from "v2" -> 2
                num = int(last_version['version_number'].replace('v', ''))
                version_number = f"v{num + 1}"
            else:
                version_number = "v1"

        # Extract text from PDF
        contract_text = self._extract_text_from_pdf(pdf_path)

        # Insert version
        self.cursor.execute("""
            INSERT INTO contract_versions (
                contract_id, version_number, version_date,
                contract_pdf_path, contract_text, uploaded_at
            ) VALUES (?, ?, date('now'), ?, ?, datetime('now'))
        """, (contract_id, version_number, pdf_path, contract_text))

        version_id = self.cursor.lastrowid
        self.conn.commit()

        return version_id

    def compare_versions(self, version_id_1: int, version_id_2: int):
        """
        Compare two contract versions and detect changes
        Returns list of changes
        """
        # Get both versions
        self.cursor.execute("""
            SELECT version_id, contract_text, version_number
            FROM contract_versions
            WHERE version_id IN (?, ?)
            ORDER BY version_id
        """, (version_id_1, version_id_2))

        versions = self.cursor.fetchall()
        if len(versions) != 2:
            return []

        old_version = versions[0]
        new_version = versions[1]

        # Perform text diff
        old_lines = old_version['contract_text'].split('\n')
        new_lines = new_version['contract_text'].split('\n')

        differ = difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm='',
            n=3  # Context lines
        )

        changes = []
        current_change = None

        for line in differ:
            if line.startswith('---') or line.startswith('+++'):
                continue
            elif line.startswith('@@'):
                # New change section
                if current_change:
                    changes.append(current_change)
                current_change = {
                    'old_text': [],
                    'new_text': [],
                    'context': line
                }
            elif line.startswith('-'):
                if current_change:
                    current_change['old_text'].append(line[1:])
            elif line.startswith('+'):
                if current_change:
                    current_change['new_text'].append(line[1:])

        if current_change:
            changes.append(current_change)

        return changes

    def detect_significant_changes(self, changes: list):
        """
        Identify significant changes (financial terms, deadlines, etc.)
        """
        significant = []

        SIGNIFICANT_KEYWORDS = [
            r'\$[\d,]+',  # Dollar amounts
            r'\d+%',  # Percentages
            r'deadline',
            r'due date',
            r'payment',
            r'liability',
            r'termination',
            r'insurance',
            r'indemnity'
        ]

        for change in changes:
            old_text = ' '.join(change['old_text'])
            new_text = ' '.join(change['new_text'])

            for keyword in SIGNIFICANT_KEYWORDS:
                if re.search(keyword, old_text, re.IGNORECASE) or \
                   re.search(keyword, new_text, re.IGNORECASE):
                    change['significant'] = True
                    change['keyword'] = keyword
                    significant.append(change)
                    break

        return significant

    def log_changes(self, contract_id: int, from_version_id: int,
                   to_version_id: int, changes: list, email_id: int = None):
        """
        Log changes to contract_change_history table
        """
        for change in changes:
            self.cursor.execute("""
                INSERT INTO contract_change_history (
                    contract_id, from_version_id, to_version_id,
                    change_type, old_text, new_text, email_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_id,
                from_version_id,
                to_version_id,
                'clause_modified' if change['old_text'] else 'clause_added',
                '\n'.join(change['old_text']),
                '\n'.join(change['new_text']),
                email_id
            ))

        self.conn.commit()

    def _extract_text_from_pdf(self, pdf_path: str):
        """Extract text from PDF (placeholder - implement with PyPDF2 or pdfplumber)"""
        # TODO: Implement PDF text extraction
        return ""
```

### Task 3: Backend Contract Version APIs

**File:** `backend/api/main.py` (add endpoints)

```python
@app.get("/api/contracts/{contract_id}/versions")
async def get_contract_versions(contract_id: int):
    """Get all versions of a contract"""
    cursor.execute("""
        SELECT
            v.version_id,
            v.version_number,
            v.version_date,
            v.is_signed,
            v.signed_date,
            v.uploaded_by,
            v.uploaded_at,
            COUNT(c.change_id) as change_count
        FROM contract_versions v
        LEFT JOIN contract_change_history c ON v.version_id = c.to_version_id
        WHERE v.contract_id = ?
        GROUP BY v.version_id
        ORDER BY v.version_id DESC
    """, (contract_id,))

    return {"versions": [dict(row) for row in cursor.fetchall()]}

@app.get("/api/contracts/versions/{version_id}/changes")
async def get_version_changes(version_id: int):
    """Get changes for a specific version"""
    cursor.execute("""
        SELECT
            c.*,
            e.subject as email_subject,
            e.sender_email
        FROM contract_change_history c
        LEFT JOIN emails e ON c.email_id = e.email_id
        WHERE c.to_version_id = ?
        ORDER BY c.change_id
    """, (version_id,))

    return {"changes": [dict(row) for row in cursor.fetchall()]}

@app.get("/api/contracts/versions/compare")
async def compare_versions(version1: int, version2: int):
    """Compare two contract versions"""
    from contract_version_detector import ContractVersionDetector

    detector = ContractVersionDetector()
    changes = detector.compare_versions(version1, version2)
    significant = detector.detect_significant_changes(changes)

    return {
        "all_changes": changes,
        "significant_changes": significant,
        "change_count": len(changes),
        "significant_count": len(significant)
    }

@app.post("/api/contracts/{contract_id}/versions")
async def upload_contract_version(contract_id: int, version: dict):
    """Upload new contract version"""
    from contract_version_detector import ContractVersionDetector

    detector = ContractVersionDetector()
    version_id = detector.add_version(
        contract_id,
        version['pdf_path'],
        version.get('version_number')
    )

    # Compare with previous version if exists
    cursor.execute("""
        SELECT version_id FROM contract_versions
        WHERE contract_id = ? AND version_id < ?
        ORDER BY version_id DESC LIMIT 1
    """, (contract_id, version_id))

    prev_version = cursor.fetchone()
    if prev_version:
        changes = detector.compare_versions(prev_version['version_id'], version_id)
        detector.log_changes(contract_id, prev_version['version_id'], version_id, changes)

    return {"success": True, "version_id": version_id}
```

### Task 4: Frontend Contract Version Viewer

**File:** `frontend/src/app/(dashboard)/contracts/[contractId]/versions/page.tsx`
```tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function ContractVersionsPage({
  params
}: {
  params: { contractId: string }
}) {
  const { data: versions } = useQuery({
    queryKey: ['contract-versions', params.contractId],
    queryFn: () => api.getContractVersions(params.contractId)
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Contract Version History</h1>

      <div className="space-y-4">
        {versions?.versions.map((version) => (
          <Card key={version.version_id}>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="text-lg">
                  {version.version_number}
                  {version.is_signed && (
                    <Badge className="ml-2" variant="success">
                      Signed
                    </Badge>
                  )}
                </CardTitle>
                <div className="text-sm text-gray-500">
                  {version.version_date}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-sm">
                  <span className="text-gray-600">Uploaded by:</span>{' '}
                  {version.uploaded_by || 'Unknown'}
                </div>
                {version.change_count > 0 && (
                  <div className="text-sm">
                    <span className="text-gray-600">Changes:</span>{' '}
                    {version.change_count} modifications
                  </div>
                )}
                {version.signed_date && (
                  <div className="text-sm">
                    <span className="text-gray-600">Signed on:</span>{' '}
                    {version.signed_date}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
```

### Task 5: Test Contract Versioning

```bash
# Test version upload
curl -X POST http://localhost:8000/api/contracts/1/versions \
  -H "Content-Type: application/json" \
  -d '{"pdf_path": "/path/to/contract_v2.pdf"}'

# Test version listing
curl http://localhost:8000/api/contracts/1/versions

# Test version comparison
curl "http://localhost:8000/api/contracts/versions/compare?version1=1&version2=2"

# Check database
sqlite3 database/bensley_master.db "SELECT * FROM contract_versions ORDER BY version_id DESC LIMIT 5"
```

---

## 📝 PHASE 5: DOCUMENTATION

Update MASTER_ARCHITECTURE.md, create completion report.

---

## 🤝 COORDINATION

**You need from Agent 1:**
- Email content for linking contract changes to email threads

**You provide to others:**
- Contract version history
- Change detection API
- Negotiation audit trail

---

## 🚫 WHAT NOT TO DO

- DON'T store entire PDF files in database (store paths only)
- DON'T create complex ML-based diff (start with simple text comparison)
- DON'T try to parse every contract format (start with common ones)

---

**STATUS:** Ready for audit
**DEPENDENCY:** None (standalone system)

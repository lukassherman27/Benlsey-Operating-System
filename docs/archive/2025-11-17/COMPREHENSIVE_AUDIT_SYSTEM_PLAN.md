# Comprehensive Project Audit & Tracking System - PHASE 2

**Status:** Planning → Implementation
**Estimated Time:** 10-15 hours
**Goal:** Full project data integrity audit with continuous learning

---

## 🎯 USER REQUIREMENTS

### **What the User Wants:**
A comprehensive system that audits every project/proposal and verifies:

1. **Project Classification**
   - Is it in the right place (proposals vs projects table)?
   - Correct status (active, proposal, completed, etc.)?

2. **Invoice & Contract Data**
   - All invoices linked to correct projects
   - Contract data imported and verified
   - Fee amounts match contracts

3. **Scope Verification**
   - Is this Landscape, Interiors, Architecture, or combination?
   - Fee breakdown per discipline
   - Does scope match actual work?

4. **Fee Structure by Phase**
   - **Mobilization** - Paid on contract signing
   - **Concept** - 3-4 months
   - **Schematic** - 1 month
   - **Design Development** - 4 months
   - **Construction Drawings** - 3-4 months
   - **Construction Observation** - Until contract end

5. **Timeline Tracking**
   - When should each phase start/end?
   - When are presentations due?
   - Total contract term
   - Are we on schedule?

6. **Continuous Learning**
   - As new data imported (invoices, contracts) → Auto re-audit
   - AI asks user for confirmation
   - User provides context/corrections
   - System learns and improves over time

---

## 📊 ENHANCED DATABASE SCHEMA

### **New Tables to Create:**

#### 1. `project_scope` - What we're actually doing
```sql
CREATE TABLE project_scope (
    scope_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    discipline TEXT NOT NULL,  -- 'landscape', 'interiors', 'architecture'
    fee_usd REAL,
    percentage_of_total REAL,
    confirmed_by_user INTEGER DEFAULT 0,
    created_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);
```

#### 2. `project_fee_breakdown` - Fee by phase
```sql
CREATE TABLE project_fee_breakdown (
    breakdown_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    phase TEXT NOT NULL,  -- 'mobilization', 'concept', 'schematic', 'dd', 'cd', 'ca'
    phase_fee_usd REAL,
    percentage_of_total REAL,
    payment_status TEXT,  -- 'pending', 'invoiced', 'paid'
    confirmed_by_user INTEGER DEFAULT 0,
    created_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);
```

#### 3. `project_phase_timeline` - Timeline tracking
```sql
CREATE TABLE project_phase_timeline (
    timeline_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    phase TEXT NOT NULL,
    expected_duration_months INTEGER,
    start_date DATE,
    expected_end_date DATE,
    actual_end_date DATE,
    presentation_date DATE,
    status TEXT,  -- 'not_started', 'in_progress', 'completed', 'delayed'
    confirmed_by_user INTEGER DEFAULT 0,
    created_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);
```

#### 4. `contract_terms` - Contract metadata
```sql
CREATE TABLE contract_terms (
    contract_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    contract_signed_date DATE,
    contract_start_date DATE,
    total_contract_term_months INTEGER,
    contract_end_date DATE,
    total_fee_usd REAL,
    payment_schedule TEXT,  -- JSON
    confirmed_by_user INTEGER DEFAULT 0,
    created_at DATETIME,
    FOREIGN KEY (project_code) REFERENCES projects(project_code)
);
```

#### 5. `user_context` - Learning from user feedback
```sql
CREATE TABLE user_context (
    context_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    question_type TEXT,  -- 'scope', 'fee_breakdown', 'timeline', 'classification'
    ai_suggestion TEXT,  -- What AI thought
    user_correction TEXT,  -- What user said
    context_provided TEXT,  -- User's explanation
    confidence_before REAL,
    confidence_after REAL,
    created_at DATETIME
);
```

#### 6. `audit_rules` - Learning rules
```sql
CREATE TABLE audit_rules (
    rule_id TEXT PRIMARY KEY,
    rule_type TEXT,  -- 'scope_detection', 'fee_validation', 'timeline_validation'
    rule_logic TEXT,  -- Description of the rule
    confidence_threshold REAL,
    times_confirmed INTEGER DEFAULT 0,
    times_rejected INTEGER DEFAULT 0,
    accuracy_rate REAL,
    auto_apply_enabled INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME
);
```

---

## 🧠 ENHANCED PATTERN DETECTION

### **New Audit Checks:**

#### 1. **Scope Verification**
```python
def verify_project_scope(project):
    """
    Detect what disciplines are included based on:
    - Project name keywords ("landscape", "interiors", "architecture")
    - Contract documents
    - Invoice line items
    - Email content analysis
    - Historical patterns
    """
    suggestions = []

    # Analyze project name
    name = project['project_name'].lower()
    detected_disciplines = []

    if 'landscape' in name or 'garden' in name:
        detected_disciplines.append('landscape')
    if 'interior' in name or 'fit-out' in name:
        detected_disciplines.append('interiors')
    if 'architecture' in name or 'master plan' in name:
        detected_disciplines.append('architecture')

    # Check if scope is defined in database
    current_scope = get_project_scope(project['project_code'])

    if not current_scope and detected_disciplines:
        suggestions.append({
            'type': 'missing_scope',
            'detected_disciplines': detected_disciplines,
            'confidence': 0.75,
            'question': f"Does {project['project_code']} include {', '.join(detected_disciplines)}?"
        })

    return suggestions
```

#### 2. **Fee Breakdown Validation**
```python
def validate_fee_breakdown(project):
    """
    Verify fee breakdown makes sense:
    - Total adds up correctly
    - Phase percentages reasonable
    - Invoice amounts match breakdown
    - Payment schedule matches phases
    """
    suggestions = []

    total_fee = project['total_fee_usd']
    breakdown = get_fee_breakdown(project['project_code'])

    if breakdown:
        breakdown_total = sum([phase['fee'] for phase in breakdown])

        if abs(breakdown_total - total_fee) > 1000:  # $1K tolerance
            suggestions.append({
                'type': 'fee_mismatch',
                'breakdown_total': breakdown_total,
                'contract_total': total_fee,
                'difference': breakdown_total - total_fee,
                'confidence': 0.95,
                'question': f"Fee breakdown (${breakdown_total:,}) doesn't match contract (${total_fee:,}). Which is correct?"
            })
    else:
        # No breakdown exists - suggest creating one
        suggestions.append({
            'type': 'missing_fee_breakdown',
            'total_fee': total_fee,
            'confidence': 0.70,
            'question': f"No fee breakdown found for ${total_fee:,}. Should I create one based on standard phases?"
        })

    return suggestions
```

#### 3. **Timeline Validation**
```python
def validate_project_timeline(project):
    """
    Check if timeline makes sense:
    - Expected durations per phase
    - Contract term matches phase durations
    - Presentations scheduled appropriately
    - Delays detected
    """
    suggestions = []

    timeline = get_project_timeline(project['project_code'])
    contract = get_contract_terms(project['project_code'])

    if contract:
        # Standard phase durations
        standard_durations = {
            'mobilization': 0,  # Immediate on signing
            'concept': 3.5,  # 3-4 months
            'schematic': 1,
            'dd': 4,
            'cd': 3.5,  # 3-4 months
            'ca': None  # Until contract end
        }

        total_expected = sum([d for d in standard_durations.values() if d])

        if contract['total_contract_term_months'] < total_expected:
            suggestions.append({
                'type': 'timeline_mismatch',
                'contract_term': contract['total_contract_term_months'],
                'expected_duration': total_expected,
                'confidence': 0.85,
                'question': f"Contract term ({contract['total_contract_term_months']} months) is shorter than standard phases ({total_expected} months). Is timeline compressed?"
            })

    return suggestions
```

#### 4. **Invoice-to-Project Linking**
```python
def verify_invoice_linking(project):
    """
    Check if invoices are linked correctly:
    - All invoices for this project linked?
    - Invoice amounts match fee breakdown?
    - Payment phases correct?
    - Any missing invoices?
    """
    suggestions = []

    invoices = get_invoices_for_project(project['project_code'])
    fee_breakdown = get_fee_breakdown(project['project_code'])

    if fee_breakdown:
        # Check if invoices cover all phases
        invoiced_phases = set([inv['phase'] for inv in invoices])
        expected_phases = set([phase['phase'] for phase in fee_breakdown])

        missing_phases = expected_phases - invoiced_phases

        if missing_phases:
            suggestions.append({
                'type': 'missing_invoices',
                'missing_phases': list(missing_phases),
                'confidence': 0.80,
                'question': f"No invoices found for phases: {', '.join(missing_phases)}. Should these be invoiced?"
            })

    return suggestions
```

---

## 🔄 CONTINUOUS LEARNING SYSTEM

### **Workflow:**

```
1. Initial Audit
   ↓
2. AI makes suggestions with questions
   ↓
3. User reviews and provides answers + context
   ↓
4. System logs user correction to user_context table
   ↓
5. AI updates confidence scores and learns patterns
   ↓
6. New data imported (invoices, contracts)
   ↓
7. Auto-trigger re-audit with improved patterns
   ↓
8. Repeat cycle → System gets smarter
```

### **Learning Logic:**

```python
def learn_from_user_feedback(suggestion_id, user_decision, user_context):
    """
    Update AI patterns based on user feedback
    """
    suggestion = get_suggestion(suggestion_id)

    # Log the feedback
    save_user_context({
        'project_code': suggestion['project_code'],
        'question_type': suggestion['type'],
        'ai_suggestion': suggestion['proposed_fix'],
        'user_correction': user_decision,
        'context_provided': user_context,
        'confidence_before': suggestion['confidence']
    })

    # Update rule accuracy
    rule = get_rule_for_suggestion_type(suggestion['type'])

    if user_decision == 'approved':
        rule['times_confirmed'] += 1
    else:
        rule['times_rejected'] += 1

    # Recalculate accuracy
    rule['accuracy_rate'] = rule['times_confirmed'] / (rule['times_confirmed'] + rule['times_rejected'])

    # Enable auto-apply if accuracy > 90% and sample > 20
    if rule['accuracy_rate'] > 0.90 and (rule['times_confirmed'] + rule['times_rejected']) > 20:
        rule['auto_apply_enabled'] = 1

    update_rule(rule)

    # Extract patterns from context
    if user_context:
        extract_new_patterns(user_context, suggestion)
```

---

## 📡 NEW API ENDPOINTS

### **Scope Management:**
- `GET /api/projects/{code}/scope` - Get project scope
- `POST /api/projects/{code}/scope` - Add/update scope
- `GET /api/audit/scope-suggestions` - Get scope verification suggestions

### **Fee Breakdown:**
- `GET /api/projects/{code}/fee-breakdown` - Get fee breakdown
- `POST /api/projects/{code}/fee-breakdown` - Set fee breakdown
- `GET /api/audit/fee-suggestions` - Get fee validation suggestions

### **Timeline:**
- `GET /api/projects/{code}/timeline` - Get phase timeline
- `POST /api/projects/{code}/timeline` - Update timeline
- `GET /api/audit/timeline-suggestions` - Get timeline suggestions

### **Contract Terms:**
- `GET /api/projects/{code}/contract` - Get contract terms
- `POST /api/projects/{code}/contract` - Import contract data

### **Learning & Feedback:**
- `POST /api/audit/feedback` - Submit user feedback/context
- `GET /api/audit/learning-stats` - Get learning statistics
- `GET /api/audit/rules` - Get current audit rules

### **Re-Audit Triggers:**
- `POST /api/audit/re-audit/{code}` - Re-audit specific project
- `POST /api/audit/re-audit-all` - Re-audit entire database

---

## 🚀 IMPLEMENTATION PHASES

### **Phase 2A: Database Schema (2 hours)**
- Create new tables
- Add indexes
- Migration scripts

### **Phase 2B: Enhanced Audit Engine (4 hours)**
- Scope verification
- Fee breakdown validation
- Timeline validation
- Invoice linking verification

### **Phase 2C: Learning System (3 hours)**
- User feedback collection
- Pattern extraction
- Confidence updates
- Auto-apply logic

### **Phase 2D: API Endpoints (2 hours)**
- All new endpoints
- Testing
- Documentation

### **Phase 2E: UI Integration (3 hours - Codex)**
- Audit review interface
- Fee breakdown input
- Timeline tracking
- Feedback forms

### **Phase 2F: Testing & Refinement (1 hour)**
- End-to-end testing
- Data validation
- User acceptance

**Total: ~15 hours**

---

## 💡 EXAMPLE USER WORKFLOW

```
User: Import contract for project 24 BK-029

System:
  → Contract imported
  → Re-auditing project...
  → Found 3 suggestions:

  1. Contract shows fee breakdown:
     - Landscape: $2M
     - Interiors: $1.25M
     But database has no scope defined. Add this breakdown? [Y/N]

  2. Contract term: 18 months
     Standard phases total: 16 months
     Timeline looks reasonable. Confirm? [Y/N]

  3. Mobilization payment: $650K
     Should be paid on signing (2024-03-15).
     No invoice found. Create reminder? [Y/N]

User:
  1. Yes, add breakdown
  2. Yes, confirm
  3. Yes, reminder

System:
  → Applied changes
  → Logged your preferences
  → Next time I see "Landscape + Interiors" I'll suggest similar breakdown
  → Confidence increased from 70% → 85%
```

---

## ✅ SUCCESS CRITERIA

- ✅ Every project has verified scope
- ✅ Fee breakdowns match contracts
- ✅ Timelines tracked per phase
- ✅ All invoices linked correctly
- ✅ System learns from user feedback
- ✅ Auto-audit on new data import
- ✅ 90%+ accuracy on learned patterns

---

**Ready to start building Phase 2A!**

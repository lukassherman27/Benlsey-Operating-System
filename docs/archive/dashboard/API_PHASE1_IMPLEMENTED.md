# Bensley Intelligence API - Phase 1 (Currently Implemented)

**Base URL:** `http://localhost:8000`
**API Docs:** http://localhost:8000/docs (Swagger UI)

This document describes the **actually implemented** REST API endpoints available now for the Phase 1 proposal tracker dashboard.

---

## 🔧 **Technical Details**

- **Framework:** FastAPI
- **Database:** SQLite (via service layer)
- **Response Format:** JSON with snake_case keys (not camelCase yet)
- **CORS Enabled:** localhost:3000, localhost:3001, localhost:5173
- **No Authentication:** Not implemented yet (all endpoints public)

---

## 📊 **Proposals**

### List All Proposals
```http
GET /api/proposals
```

**Query Parameters:**
- `status` (optional): Filter by status (e.g., "proposal", "active")
- `is_active` (optional): Boolean - filter active projects
- `page` (default: 1): Page number
- `per_page` (default: 20, max: 100): Results per page
- `sort_by` (default: "health_score"): Column to sort by
- `sort_order` (default: "ASC"): "ASC" or "DESC"

**Response:**
```json
{
  "data": [
    {
      "proposal_id": 42,
      "project_code": "BK-069",
      "project_name": "Koh Samui Private Villa",
      "client_name": "Private Client",
      "status": "proposal",
      "is_active_project": 0,
      "health_score": 62.5,
      "days_since_contact": 18,
      "last_contact_date": "2024-12-20",
      "next_action": "Send revised fee proposal",
      "pm": "Brian Sherman",
      "email_count": 24,
      "document_count": 8
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 87,
    "total_pages": 5
  }
}
```

---

### Get Proposal Statistics
```http
GET /api/proposals/stats
```

**Response:**
```json
{
  "total_proposals": 87,
  "active_projects": 1,
  "healthy": 16,
  "at_risk": 50,
  "critical": 20,
  "active_last_week": 7,
  "need_followup": 0
}
```

---

### Get Unhealthy Proposals
```http
GET /api/proposals/unhealthy?threshold=50
```

**Query Parameters:**
- `threshold` (default: 50.0): Health score threshold (0-100)

**Response:**
```json
{
  "threshold": 50.0,
  "count": 20,
  "proposals": [
    {
      "project_code": "BK-069",
      "project_name": "Koh Samui Private Villa",
      "health_score": 45.5,
      "days_since_contact": 28,
      "status": "proposal",
      "recommendation": "Immediate follow-up required"
    }
  ]
}
```

---

### Get Single Proposal
```http
GET /api/proposals/{project_code}
```

**Example:** `GET /api/proposals/BK-069`

**Response:**
```json
{
  "proposal_id": 42,
  "project_code": "BK-069",
  "project_name": "Koh Samui Private Villa",
  "client_name": "Private Client",
  "status": "proposal",
  "phase": "Fee Revision",
  "is_active_project": 0,
  "health_score": 62.5,
  "win_probability": 0.55,
  "last_contact_date": "2024-12-20",
  "next_action": "Send revised fee proposal",
  "pm": "Brian Sherman",
  "email_count": 24,
  "document_count": 8,
  "created_date": "2024-11-01",
  "updated_date": "2024-12-20"
}
```

**404 Response:**
```json
{
  "detail": "Proposal BK-999 not found"
}
```

---

### Get Proposal Timeline
```http
GET /api/proposals/{project_code}/timeline
```

**Example:** `GET /api/proposals/BK-069/timeline`

**Response:**
```json
{
  "proposal": {
    "project_code": "BK-069",
    "project_name": "Koh Samui Private Villa",
    "status": "proposal"
  },
  "timeline": [
    {
      "type": "email",
      "date": "2024-12-20T08:15:00Z",
      "subject": "Revised scope discussion",
      "sender": "client@example.com",
      "email_id": 1203,
      "category": "general"
    },
    {
      "type": "document",
      "date": "2024-12-15T14:30:00Z",
      "file_name": "BK069-Contract-v2.pdf",
      "document_type": "contract",
      "document_id": 812
    }
  ],
  "emails": [
    {
      "email_id": 1203,
      "subject": "Revised scope discussion",
      "sender_email": "client@example.com",
      "date": "2024-12-20",
      "category": "general",
      "importance_score": 0.82
    }
  ],
  "documents": [
    {
      "document_id": 812,
      "file_name": "BK069-Contract-v2.pdf",
      "document_type": "contract",
      "modified_date": "2024-12-15",
      "file_size": 245120
    }
  ],
  "stats": {
    "total_emails": 24,
    "total_documents": 8,
    "timeline_events": 32
  }
}
```

---

### Get Proposal Health Details
```http
GET /api/proposals/{project_code}/health
```

**Example:** `GET /api/proposals/BK-069/health`

**Response:**
```json
{
  "project_code": "BK-069",
  "project_name": "Koh Samui Private Villa",
  "health_score": 62.5,
  "health_status": "at_risk",
  "factors": {
    "days_since_contact": 18,
    "email_activity": "moderate",
    "document_activity": "low",
    "status": "proposal"
  },
  "risks": [
    {
      "type": "contact_gap",
      "severity": "medium",
      "description": "No contact in 18 days"
    }
  ],
  "recommendation": "Schedule follow-up call to maintain momentum"
}
```

---

### Search Proposals
```http
GET /api/proposals/search?q=villa
```

**Query Parameters:**
- `q` (required): Search term (min 1 character)

**Response:**
```json
{
  "query": "villa",
  "count": 3,
  "results": [
    {
      "project_code": "BK-069",
      "project_name": "Koh Samui Private Villa",
      "client_name": "Private Client",
      "status": "proposal"
    }
  ]
}
```

---

### Update Proposal
```http
PATCH /api/proposals/{project_code}
```

**Request Body:**
```json
{
  "status": "active"
}
```

**Response:**
```json
{
  "project_code": "BK-069",
  "status": "active",
  "updated_date": "2025-01-14T10:30:00Z"
}
```

---

## 📧 **Emails**

### List All Emails
```http
GET /api/emails
```

**Query Parameters:**
- `q` (optional): Search by subject or sender email
- `category` (optional): Filter by category (e.g., "general", "design")
- `proposal_id` (optional): Filter by linked proposal ID
- `sort_by` (optional): `date`, `sender_email`, or `subject` (default `date`)
- `sort_order` (optional): `ASC` or `DESC` (default `DESC`)
- `page` (default: 1): Page number
- `per_page` (default: 20, max: 100): Results per page

**Response:**
```json
{
  "data": [
    {
      "email_id": 1203,
      "subject": "Revised scope discussion",
      "sender_email": "client@example.com",
      "date": "2024-12-20T08:15:00Z",
      "snippet": "Following up on our conversation about...",
      "category": "general",
      "subcategory": null,
      "importance_score": 0.82,
      "ai_summary": "Client requests budget adjustment for villa design",
      "project_code": "BK-069",
      "is_active_project": 0
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 389,
    "total_pages": 20
  }
}
```

---

### Get Single Email
```http
GET /api/emails/{email_id}
```

**Example:** `GET /api/emails/1203`

**Response:**
```json
{
  "email_id": 1203,
  "subject": "Revised scope discussion",
  "sender_email": "client@example.com",
  "date": "2024-12-20T08:15:00Z",
  "body_full": "Full email body...",
  "clean_body": "Cleaned email text without signatures...",
  "snippet": "Following up on our conversation...",
  "category": "general",
  "subcategory": null,
  "importance_score": 0.82,
  "ai_summary": "Client requests budget adjustment",
  "sentiment": "neutral",
  "entities": "[{\"type\": \"fee\", \"value\": 450000}]"
}
```

---

### Get Email Categories
```http
GET /api/emails/categories
```

**Response:**
```json
{
  "general": 200,
  "design": 85,
  "project_admin": 45,
  "vendor": 30,
  "internal": 29
}
```

---

### Get Category Metadata
```http
GET /api/emails/categories/list
```

**Response:**
```json
{
  "categories": [
    { "value": "contract", "label": "Contract", "count": 45 },
    { "value": "invoice", "label": "Invoice", "count": 23 },
    { "value": "design", "label": "Design", "count": 17 }
  ]
}
```

Use this endpoint to populate dropdowns dynamically (includes display labels and counts).

---

### Get Emails by Category
```http
GET /api/emails/categories/{category}?limit=50
```

**Example:** `GET /api/emails/categories/design?limit=50`

**Response:**
```json
{
  "category": "design",
  "count": 50,
  "emails": [
    {
      "email_id": 1205,
      "subject": "Concept feedback",
      "sender_email": "designer@bensley.com",
      "date": "2024-12-18",
      "importance_score": 0.75,
      "ai_summary": "Design team shares initial concepts"
    }
  ]
}
```

---

### Search Emails
```http
GET /api/emails/search?q=contract&limit=20
```

**Query Parameters:**
- `q` (required): Search term
- `limit` (default: 20, max: 100): Max results

**Response:**
```json
{
  "query": "contract",
  "count": 15,
  "results": [
    {
      "email_id": 1198,
      "subject": "Contract review comments",
      "sender_email": "client@example.com",
      "date": "2024-12-10",
      "snippet": "We've reviewed the contract draft..."
    }
  ]
}
```

---

### Get Email Statistics
```http
GET /api/emails/stats
```

**Response:**
```json
{
  "total_emails": 389,
  "processed": 120,
  "unprocessed": 269,
  "with_full_body": 350,
  "linked_to_proposals": 245
}
```

---

### Update Email Category (NEW)
```http
POST /api/emails/{email_id}/category
```

**Request Body:**
```json
{
  "category": "design",
  "subcategory": "revision",
  "feedback": "Client asked for scope clarification"
}
```

**Response:**
```json
{
  "message": "Email category updated",
  "data": {
    "email_id": 1203,
    "subject": "Revised scope discussion",
    "sender_email": "client@example.com",
    "category": "design",
    "subcategory": "revision",
    "previous_category": "general",
    "feedback": "Client asked for scope clarification"
  }
}
```

> Note: RFIs can only be assigned to emails linked to active projects. The API will reject invalid combinations.

---

## 📄 **Documents**

### List All Documents
```http
GET /api/documents
```

**Query Parameters:**
- `document_type` (optional): Filter by type (e.g., "contract", "drawing")
- `proposal_id` (optional): Filter by linked proposal
- `page` (default: 1): Page number
- `per_page` (default: 20, max: 100): Results per page

**Response:**
```json
{
  "data": [
    {
      "document_id": 812,
      "file_name": "BK069-Contract-v2.pdf",
      "file_path": "/Users/.../BK069-Contract-v2.pdf",
      "document_type": "contract",
      "file_size": 245120,
      "modified_date": "2024-12-15T14:30:00Z",
      "project_code": "BK-069"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1523,
    "total_pages": 77
  }
}
```

---

### Get Single Document
```http
GET /api/documents/{document_id}
```

**Example:** `GET /api/documents/812`

**Response:**
```json
{
  "document_id": 812,
  "file_name": "BK069-Contract-v2.pdf",
  "file_path": "/Users/.../BK069-Contract-v2.pdf",
  "document_type": "contract",
  "file_size": 245120,
  "modified_date": "2024-12-15",
  "project_code": "BK-069",
  "project_name": "Koh Samui Private Villa"
}
```

---

### Search Documents
```http
GET /api/documents/search?q=contract&limit=20
```

**Response:**
```json
{
  "query": "contract",
  "count": 42,
  "results": [
    {
      "document_id": 812,
      "file_name": "BK069-Contract-v2.pdf",
      "document_type": "contract",
      "modified_date": "2024-12-15",
      "project_code": "BK-069"
    }
  ]
}
```

---

### Get Document Types
```http
GET /api/documents/types
```

**Response:**
```json
[
  {
    "document_type": "drawing",
    "count": 542
  },
  {
    "document_type": "contract",
    "count": 87
  },
  {
    "document_type": "specification",
    "count": 156
  }
]
```

---

### Get Document Statistics
```http
GET /api/documents/stats
```

**Response:**
```json
{
  "total_documents": 1523,
  "linked_to_proposals": 892,
  "total_size_bytes": 2450000000,
  "most_common_type": "drawing"
}
```

---

## 🧠 **Natural Language Query**

### Execute Query
```http
POST /api/query
```

**Request Body:**
```json
{
  "question": "Show me all proposals from 2024"
}
```

**Response:**
```json
{
  "success": true,
  "question": "Show me all proposals from 2024",
  "results": [
    {
      "project_code": "BK-069",
      "project_name": "Koh Samui Private Villa",
      "created_date": "2024-11-01"
    }
  ],
  "count": 42,
  "sql": "SELECT * FROM proposals WHERE strftime('%Y', created_date) = '2024'",
  "params": []
}
```

**Error Response:**
```json
{
  "success": false,
  "question": "invalid query",
  "error": "Could not parse query",
  "results": []
}
```

---

### Get Query Suggestions
```http
GET /api/query/suggestions
```

**Response:**
```json
{
  "suggestions": [
    "Show me all proposals from 2024",
    "Find all documents for BK-069",
    "Which proposals have low health scores?",
    "Show me emails from this month",
    "List all contacts",
    "Find proposals for hotel clients",
    "Show me active projects",
    "What emails are unread?",
    "Find all contracts",
    "Show proposals that need follow-up"
  ],
  "types": [
    {
      "type": "proposals",
      "description": "Query proposals and projects",
      "examples": [
        "Show me all proposals",
        "Find active projects",
        "Which proposals are from 2024?"
      ],
      "filters": ["year", "status", "project_code", "active/pending/completed"]
    },
    {
      "type": "emails",
      "description": "Query emails and communication",
      "examples": [
        "Show me emails from this month",
        "Find emails for BK-069",
        "What are the unread emails?"
      ],
      "filters": ["date", "project_code", "month/week/today"]
    },
    {
      "type": "documents",
      "description": "Query documents and files",
      "examples": [
        "Find all documents for BK-069",
        "Show me PDFs",
        "What documents were modified this week?"
      ],
      "filters": ["project_code", "file_type"]
    },
    {
      "type": "contacts",
      "description": "Query contacts and people",
      "examples": [
        "List all contacts",
        "Find contacts for hotel projects"
      ],
      "filters": ["email_count", "first_seen/last_seen"]
    }
  ]
}
```

---

## 📊 **Analytics & Dashboard**

### Get Dashboard Analytics
```http
GET /api/analytics/dashboard
```

**Response:**
```json
{
  "proposals": {
    "total_proposals": 87,
    "active_projects": 1,
    "healthy": 16,
    "at_risk": 50,
    "critical": 20,
    "active_last_week": 7,
    "need_followup": 0
  },
  "emails": {
    "total_emails": 389,
    "processed": 120,
    "unprocessed": 269,
    "with_full_body": 350,
    "linked_to_proposals": 245
  },
  "documents": {
    "total_documents": 1523,
    "linked_to_proposals": 892,
    "total_size_bytes": 2450000000,
    "most_common_type": "drawing"
  },
  "timestamp": "2025-01-14T10:45:00Z"
}
```

---

## 🏥 **Health Check**

### API Health
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "services": "operational",
  "stats": {
    "total_proposals": 87,
    "active_projects": 1,
    "healthy": 16,
    "at_risk": 50,
    "critical": 20,
    "active_last_week": 7,
    "need_followup": 0
  }
}
```

---

### Root Endpoint
```http
GET /
```

**Response:**
```json
{
  "message": "Bensley Intelligence Platform API v2",
  "version": "2.0.0",
  "status": "operational",
  "docs": "/docs",
  "endpoints": {
    "proposals": "/api/proposals",
    "emails": "/api/emails",
    "documents": "/api/documents",
    "query": "/api/query",
    "analytics": "/api/analytics/dashboard"
  }
}
```

---

## 🚀 **Starting the API Server**

```bash
# From project root
uvicorn backend.api.main_v2:app --reload --port 8000

# Server starts at: http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

---

## 🔧 **Frontend Usage Examples (React/TypeScript)**

### Fetch Proposals
```typescript
const fetchProposals = async (page = 1, perPage = 20) => {
  const response = await fetch(
    `http://localhost:8000/api/proposals?page=${page}&per_page=${perPage}&sort_by=health_score&sort_order=ASC`
  );
  const data = await response.json();
  return data;
};
```

### Execute Natural Language Query
```typescript
const executeQuery = async (question: string) => {
  const response = await fetch('http://localhost:8000/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  const data = await response.json();
  return data;
};
```

### Get Dashboard Stats
```typescript
const getDashboardStats = async () => {
  const response = await fetch('http://localhost:8000/api/analytics/dashboard');
  const data = await response.json();
  return data;
};
```

---

## ⚠️ **Known Limitations (Phase 1)**

- **No Authentication:** All endpoints are public
- **No Authorization:** No role-based access control
- **No Rate Limiting:** Unlimited requests
- **Snake Case:** Responses use `snake_case` not `camelCase`
- **Limited Filtering:** Some complex filters not yet implemented
- **No Websockets:** Real-time updates not available
- **No File Upload:** Document upload not yet implemented

---

## 🔮 **Future Endpoints (Phase 2+)**

These are designed but **not yet implemented** (see API_CONTRACTS.md for full spec):
- `/api/invoices` - Invoice tracking
- `/api/payments` - Payment receipts
- `/api/meetings` - Meeting/calendar management
- `/api/staff` - Staff assignments
- `/api/rfis` - RFI management
- `/api/deliverables` - Deliverable tracking
- `/api/contracts` - Contract intelligence
- `/api/auth/login` - Authentication

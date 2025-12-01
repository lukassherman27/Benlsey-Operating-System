# Dashboard API Contracts

Target stack for consumers: Next.js 14 + React Query. Responses are JSON encoded in camelCase. All endpoints are versioned under `/api/v1`.

## Authentication

```
POST /api/v1/auth/login
Request:  { "email": "lukas@bensley.com", "password": "..." }
Response: { "token": "jwt", "expiresIn": 3600, "user": { "id": 1, "name": "Lukas Sherman", "role": "admin" } }
```

Token is passed via `Authorization: Bearer <token>` header.

---

## Proposals & Projects

### List proposals / active projects
```
GET /api/v1/proposals?status=active&limit=50&sort=health_score
Response:
{
  "items": [
    {
      "proposalId": 42,
      "projectCode": "BK-069",
      "projectName": "Koh Samui Private Villa",
      "clientName": "Private Client",
      "status": "proposal",
      "isActiveProject": false,
      "contractSignedDate": null,
      "healthScore": 62,
      "daysSinceContact": 18,
      "nextAction": "Send revised fee proposal",
      "pm": "Brian Sherman"
    }
  ],
  "pagination": { "total": 87, "limit": 50, "offset": 0 }
}
```

### Proposal detail
```
GET /api/v1/proposals/{projectCode}
Response:
{
  "projectCode": "BK-069",
  "projectName": "Koh Samui Private Villa",
  "clientName": "Private Client",
  "status": "proposal",
  "phase": "Fee Revision",
  "healthScore": 62,
  "winProbability": 0.55,
  "lastContactDate": "2025-01-03",
  "nextAction": { "label": "Send revised fee", "dueDate": "2025-01-06" },
  "team": [
    { "staffId": 3, "name": "John Doe", "role": "Designer", "allocationPct": 50 }
  ],
  "documents": [
    { "documentId": 812, "name": "Contract Draft.pdf", "type": "contract", "link": "/files/..."}
  ],
  "emails": { "linkedCount": 24, "latest": { "emailId": 1203, "subject": "Revised scope", "date": "2025-01-03" } }
}
```

### Proposal health history
```
GET /api/v1/proposals/{projectCode}/health
Response:
{
  "projectCode": "BK-069",
  "trend": [
    { "date": "2024-12-20", "healthScore": 80, "notes": "Positive meeting" },
    { "date": "2024-12-28", "healthScore": 68, "notes": "Awaiting client feedback" }
  ],
  "risks": [
    { "id": "no-contact", "description": "No contact in 18 days", "severity": "high" }
  ]
}
```

### Proposal timeline
```
GET /api/v1/proposals/{projectCode}/timeline
Response:
{
  "projectCode": "BK-069",
  "events": [
    { "timestamp": "2024-12-01T10:00:00Z", "type": "meeting", "title": "Kickoff call", "owner": "Bill" },
    { "timestamp": "2024-12-05", "type": "document", "title": "Initial proposal sent", "documentId": 801 },
    { "timestamp": "2024-12-19", "type": "email", "title": "Client questions", "emailId": 1203 }
  ]
}
```

---

## Emails & Categorization

### Categorized email feed
```
GET /api/v1/emails?category=general&proposal=BK-069&limit=25
Response:
{
  "items": [
    {
      "emailId": 1203,
      "subject": "Scope adjustments",
      "sender": "client@example.com",
      "date": "2024-12-19T08:12:00Z",
      "category": "general",
      "subcategory": "scope_discussion",
      "importanceScore": 0.82,
      "actionRequired": true,
      "followUpDate": "2024-12-21",
      "summary": "Client requested budget adjustment for villas"
    }
  ]
}
```

### Email detail (with AI analysis)
```
GET /api/v1/emails/{emailId}
Response:
{
  "emailId": 1203,
  "subject": "Scope adjustments",
  "body": "...",
  "cleanBody": "...",
  "category": "general",
  "subcategory": "scope_discussion",
  "entities": [{ "type": "fee", "value": 450000 }],
  "proposalLinks": [{ "projectCode": "BK-069", "confidence": 0.88 }]
}
```

---

## Documents

```
GET /api/v1/documents?projectCode=BK-069&documentType=contract
Response:
{
  "items": [
    {
      "documentId": 812,
      "fileName": "BK069-Contract-v2.pdf",
      "documentType": "contract",
      "version": "v2",
      "uploadedAt": "2024-12-05T12:00:00Z",
      "summary": "Second draft with revised scope",
      "linkedProposals": ["BK-069"],
      "tags": ["contract", "revision"]
    }
  ]
}
```

---

## Financials (Invoices & Payments)

### Invoices
```
GET /api/v1/invoices?status=overdue&projectCode=BK-069
Response:
{
  "items": [
    {
      "invoiceId": 301,
      "projectCode": "BK-069",
      "projectName": "Koh Samui Private Villa",
      "clientName": "Private Client",
      "amount": 250000,
      "currency": "USD",
      "issueDate": "2024-12-10",
      "dueDate": "2024-12-24",
      "status": "overdue",
      "daysPastDue": 12,
      "milestone": "50% Design Development",
      "pm": "Brian Sherman"
    }
  ]
}
```

### Payments
```
GET /api/v1/payments?dateRange=this_month
Response:
{
  "total": 450000,
  "items": [
    {
      "paymentId": 555,
      "invoiceId": 290,
      "projectCode": "BK-052",
      "amount": 150000,
      "receivedDate": "2025-01-02",
      "method": "wire",
      "reference": "HSBC-90231"
    }
  ]
}
```

### Revenue analytics
```
GET /api/v1/analytics/revenue?groupBy=week
Response:
{
  "series": [
    { "period": "2024-W51", "actual": 200000, "projected": 280000 },
    { "period": "2024-W52", "actual": 150000, "projected": 250000 }
  ],
  "ytd": { "actual": 3_200_000, "target": 4_500_000 }
}
```

---

## Meetings & Schedule

```
GET /api/v1/meetings?date=2024-12-19
Response:
{
  "items": [
    {
      "meetingId": 88,
      "title": "Client Coordination",
      "projectCode": "BK-069",
      "projectName": "Koh Samui Private Villa",
      "participants": ["Bill Bensley", "Client CEO"],
      "scheduledFor": "2024-12-19T10:00:00+07:00",
      "location": "Teams",
      "agenda": "Review scope revisions",
      "relatedDeliverables": [1205]
    }
  ]
}
```

---

## Staff & Assignments

```
GET /api/v1/staff
Response:
{
  "items": [
    {
      "staffId": 3,
      "name": "John Doe",
      "role": "Project Manager",
      "currentLoadPct": 85,
      "projects": [
        { "projectCode": "BK-069", "allocationPct": 50, "nextDeliverable": "CD package 11/22" },
        { "projectCode": "BK-055", "allocationPct": 35, "nextDeliverable": "RFI responses" }
      ]
    }
  ]
}
```

Assignments CRUD:
```
POST /api/v1/projects/{projectCode}/assignments
Body: { "staffId": 3, "role": "PM", "allocationPct": 50 }
```

---

## RFIs & Deliverables

```
GET /api/v1/rfis?status=overdue
Response:
{
  "items": [
    {
      "rfiId": 12,
      "projectCode": "BK-055",
      "title": "Structural question #3",
      "status": "overdue",
      "dueDate": "2024-12-15",
      "assignedTo": "John Doe",
      "daysOverdue": 4,
      "reason": "Waiting on consultant input"
    }
  ]
}
```

Deliverables feed:
```
GET /api/v1/deliverables?projectCode=BK-069
Response:
{
  "items": [
    {
      "deliverableId": 710,
      "name": "100% CD Presentation",
      "owner": "Design Team",
      "status": "scheduled",
      "scheduledDate": "2024-11-22",
      "linkedInvoice": 402,
      "autoInvoiceAmount": 300000
    }
  ]
}
```

---

## Contracts & Scope Intelligence

```
GET /api/v1/contracts/{projectCode}
Response:
{
  "projectCode": "BK-069",
  "feeSchedule": [
    { "milestone": "Concept Design 30%", "amount": 180000, "invoiceId": 250 },
    { "milestone": "100% CD 40%", "amount": 240000, "expectedDate": "2024-11-22" }
  ],
  "scopeItems": [
    {
      "itemId": 901,
      "description": "Landscape master plan",
      "included": true,
      "notes": "Includes hardscape layout",
      "sourceDocumentId": 812
    }
  ],
  "changeOrders": [
    { "changeOrderId": 12, "description": "Add lighting package", "amount": 35000 }
  ]
}
```

---

## Query Brain

```
POST /api/v1/query
Body: { "query": "Did BK-069 include lighting design?" }
Response:
{
  "query": "Did BK-069 include lighting design?",
  "answer": "Lighting design is covered under Change Order #12 dated 2024-10-05.",
  "sources": [
    { "type": "document", "documentId": 9001, "excerpt": "Scope: includes exterior lighting" },
    { "type": "email", "emailId": 1234, "excerpt": "Client approved lighting change order." }
  ],
  "sqlExecuted": "...",
  "confidence": 0.78
}
```

---

## Dashboard Analytics Endpoint

```
GET /api/v1/analytics/dashboard
Response:
{
  "proposalPipeline": {
    "active": 22,
    "negotiating": 8,
    "atRisk": 5,
    "winsThisMonth": 2
  },
  "financials": {
    "invoicesDueThisWeek": 5,
    "overdueAmount": 420000,
    "paymentsReceivedThisMonth": 610000,
    "projectedMonthEnd": 920000
  },
  "operations": {
    "meetingsToday": 4,
    "deliverablesDueThisWeek": 7,
    "rfisOverdue": 3,
    "staffUtilization": 0.82
  }
}
```

---

## Webhooks / Notifications

```
POST /api/v1/webhooks/events
Body: { "type": "invoice.overdue", "data": { "invoiceId": 301, "projectCode": "BK-069" } }
```

Use for Slack/email alerts or cron status pings.

---

These contracts cover the full vision so the frontend can design components with future functionality in mind while Phase 1 focuses on proposals, emails, documents, and query results.

# RBAC Implementation Agent - Role-Based Access Control

> Issue: #318 | Priority: P1 | Branch: `feat/rbac-implementation-318`

---

## CONTEXT

Currently everyone sees everything. No role-based filtering exists.

Roles needed:
| Role | Who | What They See |
|------|-----|---------------|
| Executive | Bill, Brian | Everything (read-only mostly) |
| Director | Lukas | Full CRUD + admin |
| PM | Astuti, Brian K | Their projects only |
| Designer | 95 staff | None (email-based, future) |
| Finance | TBD | Invoices only |

Auth system exists (NextAuth) but middleware is DISABLED.

---

## PHASE 1: UNDERSTAND (Research First)

### Required Research
```bash
# Check existing auth setup
cat frontend/src/middleware.ts
cat frontend/src/auth.ts | head -50

# Check staff table schema
sqlite3 database/bensley_master.db ".schema staff"

# Check if roles exist anywhere
grep -r "role\|RBAC" backend/api --include="*.py" | head -20

# Check dependencies.py
cat backend/api/dependencies.py | head -100
```

### Questions to Answer
1. Is NextAuth v4 or v5?
2. Does staff table have role column already?
3. How is `current_user` passed to API endpoints?
4. Which endpoints need role filtering?

### Files to Read
- `frontend/src/auth.ts` - Auth configuration
- `frontend/src/middleware.ts` - Currently disabled
- `backend/api/dependencies.py` - Auth dependency injection
- `backend/api/routers/projects.py` - Example needing filtering

**STOP HERE** until you understand the auth state.

---

## PHASE 2: THINK HARD (Planning)

### Design Decisions
1. **Role storage** - Column on staff vs separate table?
2. **Permission granularity** - Role-based vs permission-based?
3. **Frontend vs Backend** - Where to enforce?
4. **Middleware scope** - All routes or selective?

### Web Research
```
Search: "NextAuth v5 role-based access control"
Search: "FastAPI RBAC middleware patterns"
```

### Recommended Approach
1. Add `role` column to staff (simple, no join)
2. Role-based for simplicity
3. Enforce on BOTH frontend and backend
4. Selective middleware (some routes public)

---

## PHASE 3: IMPLEMENT

### Database Migration
```sql
ALTER TABLE staff ADD COLUMN role TEXT DEFAULT 'viewer'
  CHECK (role IN ('executive', 'director', 'pm', 'designer', 'finance', 'viewer'));

UPDATE staff SET role = 'executive' WHERE name LIKE '%Bensley%' OR name LIKE 'Brian Petrie%';
UPDATE staff SET role = 'director' WHERE name LIKE '%Lukas%';
UPDATE staff SET role = 'pm' WHERE is_pm = 1;
UPDATE staff SET role = 'designer' WHERE department = 'Design' AND role = 'viewer';
```

### Backend Role Dependency
```python
# backend/api/dependencies.py
def require_role(*allowed_roles: str):
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Role not authorized")
        return current_user
    return role_checker
```

### Frontend Middleware
```typescript
// frontend/src/middleware.ts
export default auth((req) => {
  const { pathname } = req.nextUrl
  const session = req.auth

  if (!session && !pathname.startsWith('/login')) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  const adminRoutes = ['/admin', '/settings']
  if (adminRoutes.some(r => pathname.startsWith(r))) {
    if (session?.user?.role !== 'director') {
      return NextResponse.redirect(new URL('/', req.url))
    }
  }

  return NextResponse.next()
})
```

### Frontend RoleGate Component
```typescript
// frontend/src/components/auth/role-gate.tsx
export function RoleGate({ allowedRoles, children, fallback = null }) {
  const { data: session } = useSession()
  if (!allowedRoles.includes(session?.user?.role)) return fallback
  return <>{children}</>
}
```

### Files to Create/Modify
| File | Action | Purpose |
|------|--------|---------|
| `scripts/migrations/add_role_column.sql` | Create | Database migration |
| `backend/api/dependencies.py` | Modify | Add require_role |
| `frontend/src/middleware.ts` | Modify | Enable auth |
| `frontend/src/components/auth/role-gate.tsx` | Create | UI role gating |

---

## PHASE 4: VERIFY

### Testing Checklist
- [ ] Database has role column
- [ ] API returns 403 for unauthorized access
- [ ] PM user only sees assigned projects
- [ ] Director can access admin routes
- [ ] Unauthenticated redirected to login

### Verification Commands
```bash
sqlite3 database/bensley_master.db "SELECT name, role FROM staff WHERE role IS NOT NULL LIMIT 10;"
cd frontend && npm run build
```

### Success Criteria
- All staff have role assigned
- API endpoints enforce role access
- Frontend redirects unauthorized
- No regressions

---

## PHASE 5: COMPLETE

### Commit Format
```bash
git commit -m "feat(auth): implement role-based access control (#318)

- Add role column to staff table
- Create require_role() dependency
- Enable NextAuth middleware
- Add RoleGate component

Fixes #318"
```

---

## CONSTRAINTS

- **Don't lock out Lukas** - Must remain director
- **Don't break existing auth** - Test thoroughly
- **Start permissive** - Default to 'viewer'
- **Log access attempts** - For auditing

---

## RESOURCES

- `.claude/plans/system-architecture-ux.md` - Section 3: Roles & Permissions
- Issue #318 for scope
- NextAuth v5 docs: https://authjs.dev/

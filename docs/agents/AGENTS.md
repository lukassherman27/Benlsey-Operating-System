# Repository Guidelines

## Project Structure & Module Organization
- `backend/` – FastAPI services (`api/` entrypoints, `services/` data layer, `core/` legacy scripts, `routes/` Flask-to-FastAPI migration).  
- `frontend/` – Next.js dashboard (React components under `src/components`, pages in `src/app`, utilities in `src/lib`).  
- `database/` – SQLite schema, migrations, and helper scripts; production DB lives outside the repo (`~/Desktop/BDS_SYSTEM/...`).  
- `reports/`, `docs/`, `scripts/` – Generated CSVs/audits, architecture notes, and operational helpers. Keep generated artifacts out of version control whenever possible.

## Build, Test, and Development Commands
- **Backend dev server**  
  ```bash
  source venv/bin/activate
  uvicorn backend.api.main_v2:app --reload --host 127.0.0.1 --port 8000
  ```
  Loads FastAPI with hot reload against the real SQLite DB.
- **Frontend dev server**  
  ```bash
  cd frontend
  export NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
  npm install        # first run only
  npm run dev -- --port 3002
  ```
  Serves the dashboard and proxies API calls using the env var above.
- Run Python scripts with `python3 path/to/script.py` inside the repo root after activating `venv`.

## Coding Style & Naming Conventions
- Python: Black-style 4‑space indentation, snake_case for functions, PascalCase for classes. Prefer services accessing the DB via `BaseService`.  
- TypeScript/React: Prettier/Turbo defaults, components in PascalCase, hooks `useSomething`. Separate UI primitives under `components/ui`.  
- Filenames should reflect their responsibility (`*_service.py`, `*-panel.tsx`). Avoid camelCase directories.

## Testing Guidelines
- Backend tests currently focus on ad-hoc validation via scripts (see `backend/services/test_services.py`). When adding pytest suites, place them under `backend/tests/` and name files `test_<module>.py`.  
- Frontend testing is manual today; if you add vitest/playwright, keep specs alongside components (`component.test.tsx`). Always verify `/health`, `/api/decision-tiles`, and `/api/finance/*` before PRs.

## Commit & Pull Request Guidelines
- Commit messages follow “component: summary” (e.g., `frontend: wire decision tiles`). Keep commits scoped and reference migrations/import tools when applicable.  
- Pull requests should include: purpose, screenshots of UI changes (desktop + mobile), backend API contracts touched (`/api/...`), and any migration or data-move steps. Link to Linear/Jira issues when known and call out verification steps (commands run, endpoints tested).  
- Avoid committing generated DB files or large CSV exports; place them under `reports/archive/` and add to `.gitignore` if needed.

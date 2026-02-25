# Ondo — Data Governance & Dataset Readiness Platform

## Architecture

- **Backend:** FastAPI (Python 3.11+), SQLAlchemy ORM, PostgreSQL (Alembic migrations)
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Monorepo:** `backend/` and `frontend/` directories at root
- **Container Runtime:** Podman (via Makefile targets)

## Running Locally

```bash
# Using Makefile (recommended)
make start    # Starts PostgreSQL, runs migrations, seeds data, starts backend + frontend
make stop     # Stops everything

# Manual
cd backend
docker compose up -d          # PostgreSQL
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

cd frontend
npm install
npm run dev
```

## Backend Conventions

### API Routes
- All routes live under `backend/app/api/` — one module per domain.
- Routers are prefixed with `/api/<domain>` and included in `main.py`.
- Response schemas live in `backend/app/api/schemas.py` (Pydantic v2, `from_attributes = True`).

**Current API modules:**
| Module | Prefix | Purpose |
|--------|--------|---------|
| `datasets.py` | `/api/datasets` | CRUD, list (paginated), export (CSV/JSON), metadata, tags, classification |
| `ai.py` | `/api/ai` | AI-assisted descriptions and schema generation |
| `ingest.py` | `/api/ingest` | Mock data, dbt manifest/catalog upload, generic metadata push |
| `health.py` | `/api/health` | Health check |
| `dashboard.py` | `/api/dashboard` | Summary stats, score distribution, trends |
| `quality.py` | `/api/datasets/{id}/quality-rules` | Quality rule CRUD and execution recording |
| `profiling.py` | `/api/datasets/{id}/profiles` | Column profiling data submission and retrieval |
| `glossary.py` | `/api/glossary` | Business glossary terms CRUD, column linking |
| `notifications.py` | `/api/notifications` | Watch/unwatch datasets, notification listing |
| `usage.py` | `/api/datasets/{id}/usage` | View tracking and usage statistics |
| `bulk.py` | `/api/datasets/bulk` | Bulk operations (delete, update owner/status/tags) |
| `schema_changes.py` | `/api/datasets/{id}/schema` | Schema snapshots and change detection |
| `audit.py` | `/api/audit` | Audit log listing and filtering |

### Response Builders
- Shared response-building logic lives in `backend/app/api/response_builder.py`.
- `build_dataset_detail_response(db, dataset_id)` is the single way to construct a `DatasetDetailResponse` — used by `datasets.py` and `ai.py`.
- Converter functions (`column_to_response`, etc.) are exported from `response_builder.py`.

### Scoring Constants
- `backend/app/scoring/constants.py` defines stable `ActionKey` and `ReasonCode` constants (versioned v1).
- `ACTION_KEY_TO_DIMENSION` mapping lives in `response_builder.py`, built from `ActionKey`.
- **Do NOT change constant values** — they are part of the API contract.

### Audit Logging
- `backend/app/services/audit.py` provides `log_audit(db, dataset_id, action, actor, details)`.
- Called from `datasets.py` (owner/metadata changes), `scoring_service.py` (score changes).
- Stored in `audit_log` table.

### Logging
- `logging.basicConfig()` is configured in `main.py` at INFO level.
- Each module uses `logger = logging.getLogger(__name__)`.

### DB Sessions
- `get_db()` dependency yields a session per request — never create sessions manually.
- `measured` field on `DatasetDimensionScore` is stored as INTEGER (1/0) for SQLite compat.

## Frontend Conventions

### Pages
| Route | File | Purpose |
|-------|------|---------|
| `/` | `app/page.tsx` | Dashboard — metrics, score distribution, trends, needs-attention |
| `/datasets` | `app/datasets/page.tsx` | Dataset list with filters, pagination, bulk actions |
| `/datasets/[id]` | `app/datasets/[id]/page.tsx` | Dataset detail with tabbed interface |
| `/browse` | `app/browse/page.tsx` | Browse datasets by group (domain, classification, location, status) |
| `/glossary` | `app/glossary/page.tsx` | Business glossary term management |

### Shared Components
- `NavBar.tsx` — Responsive nav with active highlighting, hamburger menu (mobile), ThemeToggle, NotificationBell
- `ThemeToggle.tsx` — Dark/light mode toggle, persists to localStorage
- `NotificationBell.tsx` — Notification dropdown with unread badge

### Shared Utils
- `frontend/app/lib/dataset-utils.tsx` contains all shared utility functions:
  - Location helpers: `getLocationIcon()`, `getLocationLabel()`, `getLocationBadgeColor()`
  - Status helpers: `getStatusBadgeClass()`, `getStatusLabel()`
  - Dimension helpers: `getDimensionLabel()`, `ACTION_KEY_TO_DIMENSION`
  - Formatters: `formatDataSize()`, `formatSLA()`
- **Import from here** — never duplicate these functions in components.

### API Client
- `frontend/app/api/client.ts` — typed fetch wrappers for all backend endpoints.
- Interfaces match backend Pydantic schemas.

### Tab Components (Dataset Detail)
- Split into tab components under `frontend/app/datasets/[id]/components/`:
  - `OverviewTab.tsx` — Metadata, tags, classification, owner
  - `ScoreAnalysisTab.tsx` — Dimension scores and recommended actions
  - `SchemaTab.tsx` — Column list with profiling, glossary term linking, schema change history
  - `LineageTab.tsx` — Visual lineage graph, upstream/downstream, impact analysis
  - `QualityTab.tsx` — Quality rule management and execution history
  - `UsageTab.tsx` — View stats with period selector and charts
  - `ActivityTab.tsx` — Audit log timeline with action icons
  - `DetailsTab.tsx` — Raw metadata and configuration
- `DatasetContent.tsx` is the orchestrator (header, export dropdown, tab bar, tab routing).
- Tab type union: `'overview' | 'score' | 'schema' | 'lineage' | 'quality' | 'usage' | 'activity' | 'details'`

### Dark Mode
- Tailwind `darkMode: 'class'` in `tailwind.config.js`.
- Theme persisted to localStorage, respects `prefers-color-scheme`.
- All components use `dark:` Tailwind variants for dark mode styles.
- `suppressHydrationWarning` on `<html>` element in `layout.tsx` for SSR safety.

### TypeScript
- Strict mode enabled. Avoid `any` — use proper types.

## Database Conventions

- Migrations managed via Alembic (`backend/alembic/`).
- The `measured` field is INTEGER (1=true, 0=false) for SQLite compatibility — convert in application code.
- UUIDs are PostgreSQL `UUID` type with `as_uuid=True`.

**Current migration chain (17 migrations):**
`001_initial_schema` → `3fce7f10f30b` (columns) → `502e02ad3bda` (measured) → `5dd8395d8b24` (description) → `6a1b2c3d4e5f` (location) → `7f8a9b0c1d2e` (lineage) → `8a9b0c1d2e3f` (metadata fields) → `9b0c1d2e3f4a` (data_size_bytes fix) → `a0b1c2d3e4f5` (created/updated by) → `b1c2d3e4f5a6` (tags/classification) → `c2d3e4f5a6b7` (quality rules) → `d3e4f5a6b7c8` (column profiles) → `e4f5a6b7c8d9` (glossary) → `f5a6b7c8d9e0` (search/watches) → `g6b7c8d9e0f1` (usage metrics) → `h7b8c9d0e1f2` (schema snapshots) → `i8c9d0e1f2g3` (audit log)

**Key tables (beyond core datasets/columns/scores):**
- `dataset_tags`, `quality_rules`, `quality_rule_executions`, `column_profiles`
- `glossary_terms`, `glossary_column_links`
- `dataset_lineage`, `dataset_watches`, `notifications`
- `dataset_views`, `schema_snapshots`, `schema_changes`, `audit_log`

## Testing

```bash
cd backend && python -m pytest tests/ -v
cd frontend && npm run build                    # TypeScript compilation check
cd frontend && npx playwright test              # E2E smoke tests (requires dev server)
```

- E2E tests live in `frontend/e2e/smoke.spec.ts` — smoke tests for page loads, navigation, search, dark mode toggle.
- Playwright config at `frontend/playwright.config.ts` — uses `http://localhost:3000`, starts dev server automatically.
- `playwright.config.ts` and `e2e/` are excluded from `tsconfig.json` compilation.

## What NOT to Change

- **API contract v1:** Response shapes in `schemas.py`, `ActionKey`/`ReasonCode` constants.
- **Scoring constants:** Point values and status thresholds in `scoring/`.
- **CORS `allow_origins=["*"]`:** Fix when deploying to production, not during refactoring.
- **Migration revision IDs:** These are part of the Alembic chain. Always chain new migrations from the latest (`i8c9d0e1f2g3`).

## Feature Status (All Complete)

All 8 governance phases and 12 platform improvements have been implemented:

**Governance (Phase 1-8):** Tags/classification, dashboard, quality rules, data profiling, dbt/metadata connectors, business glossary, enhanced search, notifications/watches

**Platform improvements:** Active nav highlighting, usage tab, responsive layout, empty states, schema change detection, descriptions on list pages, glossary linking in schema, CSV/JSON export, pagination, audit log, dark mode, E2E tests

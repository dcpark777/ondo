# Ondo — Dataset Readiness Scoring Platform

## Architecture

- **Backend:** FastAPI (Python 3.11+), SQLAlchemy ORM, PostgreSQL (Alembic migrations)
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Monorepo:** `backend/` and `frontend/` directories at root

## Running Locally

```bash
# Backend
cd backend
docker compose up -d          # PostgreSQL
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Backend Conventions

### API Routes
- All routes live under `backend/app/api/` — one module per domain (datasets, ai, ingest, health).
- Routers are prefixed with `/api/<domain>` and included in `main.py`.
- Response schemas live in `backend/app/api/schemas.py` (Pydantic v2, `from_attributes = True`).

### Response Builders
- Shared response-building logic lives in `backend/app/api/response_builder.py`.
- `build_dataset_detail_response(db, dataset_id)` is the single way to construct a `DatasetDetailResponse` — used by `datasets.py` and `ai.py`.
- Converter functions (`column_to_response`, etc.) are exported from `response_builder.py`.

### Scoring Constants
- `backend/app/scoring/constants.py` defines stable `ActionKey` and `ReasonCode` constants (versioned v1).
- `ACTION_KEY_TO_DIMENSION` mapping lives in `response_builder.py`, built from `ActionKey`.
- **Do NOT change constant values** — they are part of the API contract.

### Logging
- `logging.basicConfig()` is configured in `main.py` at INFO level.
- Each module uses `logger = logging.getLogger(__name__)`.

### DB Sessions
- `get_db()` dependency yields a session per request — never create sessions manually.
- `measured` field on `DatasetDimensionScore` is stored as INTEGER (1/0) for SQLite compat.

## Frontend Conventions

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

### Tab Components
- Dataset detail page is split into tab components under `frontend/app/datasets/[id]/components/`:
  - `OverviewTab.tsx`, `ScoreAnalysisTab.tsx`, `SchemaTab.tsx`, `LineageTab.tsx`, `DetailsTab.tsx`
  - `DatasetContent.tsx` is the thin orchestrator (header, tab bar, tab routing).

### TypeScript
- Strict mode enabled. Avoid `any` — use proper types.

## Database Conventions

- Migrations managed via Alembic (`backend/alembic/`).
- The `measured` field is INTEGER (1=true, 0=false) for SQLite compatibility — convert in application code.
- UUIDs are PostgreSQL `UUID` type with `as_uuid=True`.

## Testing

```bash
cd backend && python -m pytest tests/ -v
cd frontend && npm run build   # TypeScript compilation check
```

## What NOT to Change

- **API contract v1:** Response shapes in `schemas.py`, `ActionKey`/`ReasonCode` constants.
- **Scoring constants:** Point values and status thresholds in `scoring/`.
- **CORS `allow_origins=["*"]`:** Fix when deploying to production, not during refactoring.

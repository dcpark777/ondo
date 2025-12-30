# Ondo MVP Build Plan

This document outlines a step-by-step build plan for the Ondo MVP, with each milestone producing a runnable demo.

## Overview

Ondo is a SaaS that scores datasets for data product readiness (0-100 score) and provides actionable improvements. The MVP will be built incrementally with demoable milestones.

---

## Milestone 1: Project Setup & Database Schema
**Goal:** Working database with schema migrations  
**Demo:** Database initialized, migrations run successfully

### Files to Create:
```
backend/
├── pyproject.toml (or requirements.txt)
├── README.md
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
├── app/
│   ├── __init__.py
│   ├── main.py (FastAPI app entry)
│   ├── config.py (database config)
│   └── models.py (SQLAlchemy models)
└── .env.example
```

### Files to Modify:
- None (initial setup)

### Tasks:
1. Initialize Python project with FastAPI, SQLAlchemy 2.0, Alembic, psycopg2
2. Create database models for:
   - `datasets`
   - `dataset_dimension_scores`
   - `dataset_reasons`
   - `dataset_actions`
   - `dataset_score_history`
3. Create Alembic migration for initial schema
4. Add database connection config
5. Test: Run migrations, verify tables created

### Demo Command:
```bash
cd backend && alembic upgrade head && python -c "from app.models import *; print('Schema ready')"
```

---

## Milestone 2: Basic API Server & Health Check
**Goal:** Running FastAPI server with health endpoint  
**Demo:** `curl http://localhost:8000/health` returns 200 OK

### Files to Create:
```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py
│   └── db.py (database session dependency)
```

### Files to Modify:
```
backend/
└── app/
    └── main.py (add health router)
```

### Tasks:
1. Create FastAPI app instance
2. Add database session dependency
3. Implement GET /health endpoint
4. Add CORS middleware for frontend
5. Test: Start server, hit health endpoint

### Demo Command:
```bash
cd backend && uvicorn app.main:app --reload
# In another terminal: curl http://localhost:8000/health
```

---

## Milestone 3: Scoring Engine Core
**Goal:** Deterministic scoring function with all 6 dimensions  
**Demo:** Given mock dataset metadata, compute score + reasons + actions

### Files to Create:
```
backend/
├── app/
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── engine.py (main scoring orchestrator)
│   │   ├── dimensions/
│   │   │   ├── __init__.py
│   │   │   ├── ownership.py
│   │   │   ├── documentation.py
│   │   │   ├── schema_hygiene.py
│   │   │   ├── data_quality.py
│   │   │   ├── stability.py
│   │   │   └── operational.py
│   │   └── types.py (scoring result types)
└── tests/
    ├── __init__.py
    └── test_scoring.py
```

### Files to Modify:
- None (new module)

### Tasks:
1. Create scoring result types (ScoreResult, DimensionScore, Reason, Action)
2. Implement each dimension scorer:
   - Ownership & Accountability (15 pts)
   - Documentation Quality (20 pts)
   - Schema Hygiene (15 pts)
   - Data Quality Signals (20 pts)
   - Stability & Change Management (20 pts)
   - Operational Metadata (10 pts)
3. Create main scoring engine that orchestrates all dimensions
4. Map total score to status (Draft/Internal/Production-Ready/Gold)
5. Write unit tests for scoring engine

### Demo Command:
```bash
cd backend && python -m pytest tests/test_scoring.py -v
# Or: python -c "from app.scoring.engine import score_dataset; print(score_dataset(mock_data))"
```

---

## Milestone 4: Dataset CRUD API
**Goal:** Create, read, update datasets via API  
**Demo:** POST dataset, GET dataset list, GET dataset detail

### Files to Create:
```
backend/
├── app/
│   ├── api/
│   │   ├── datasets.py
│   │   └── schemas.py (Pydantic models for request/response)
│   └── services/
│       ├── __init__.py
│       └── dataset_service.py (business logic)
```

### Files to Modify:
```
backend/
└── app/
    └── main.py (add datasets router)
```

### Tasks:
1. Create Pydantic schemas for:
   - DatasetCreate, DatasetUpdate, DatasetResponse
   - DimensionScoreResponse, ReasonResponse, ActionResponse
2. Implement dataset service with CRUD operations
3. Create API endpoints:
   - GET /api/datasets (list with filtering)
   - GET /api/datasets/{id} (detail)
   - POST /api/datasets (create)
4. Add OpenAPI documentation
5. Test: Create dataset via API, retrieve it

### Demo Command:
```bash
# Start server, then:
curl -X POST http://localhost:8000/api/datasets \
  -H "Content-Type: application/json" \
  -d '{"full_name": "analytics.users", "display_name": "Users Table"}'
curl http://localhost:8000/api/datasets
```

---

## Milestone 5: Scoring Integration & Persistence
**Goal:** Score datasets and save results to database  
**Demo:** Create dataset, trigger scoring, view score in database

### Files to Create:
```
backend/
├── app/
│   └── services/
│       └── scoring_service.py (orchestrates scoring + persistence)
```

### Files to Modify:
```
backend/
├── app/
│   ├── api/
│   │   └── datasets.py (add scoring trigger)
│   └── services/
│       └── dataset_service.py (integrate scoring)
```

### Tasks:
1. Create scoring service that:
   - Takes dataset metadata
   - Calls scoring engine
   - Saves dimension scores, reasons, actions to DB
   - Updates dataset readiness_score and readiness_status
   - Records in score history
2. Integrate scoring into dataset creation/update flows
3. Add endpoint: POST /api/datasets/{id}/score (manual trigger)
4. Test: Create dataset, verify score calculated and persisted

### Demo Command:
```bash
# Create dataset, then:
curl -X POST http://localhost:8000/api/datasets/{id}/score
curl http://localhost:8000/api/datasets/{id}
# Verify score, status, reasons, actions in response
```

---

## Milestone 6: Mock Data Ingestion
**Goal:** Seed demo datasets with realistic metadata  
**Demo:** Ingest mock data, see multiple scored datasets

### Files to Create:
```
backend/
├── app/
│   ├── api/
│   │   └── ingest.py
│   └── services/
│       └── mock_ingestion.py
└── app/
    └── data/
        └── mock_datasets.json (sample data)
```

### Files to Modify:
```
backend/
└── app/
    └── main.py (add ingest router)
```

### Tasks:
1. Create mock dataset generator with varied scores:
   - High-scoring dataset (Gold status)
   - Medium-scoring dataset (Production-Ready)
   - Low-scoring dataset (Draft)
2. Implement POST /api/ingest/mock endpoint
3. Generate realistic metadata (columns, owners, docs, etc.)
4. Ingest and score all mock datasets
5. Test: Ingest mock data, verify datasets appear with scores

### Demo Command:
```bash
curl -X POST http://localhost:8000/api/ingest/mock
curl http://localhost:8000/api/datasets
# See multiple datasets with different scores
```

---

## Milestone 7: Dataset Metadata Update Endpoints
**Goal:** Update owner, contact, intended use, limitations  
**Demo:** Update dataset metadata, see score change

### Files to Modify:
```
backend/
├── app/
│   ├── api/
│   │   └── datasets.py (add update endpoints)
│   └── services/
│       └── dataset_service.py (add update methods)
```

### Tasks:
1. Implement POST /api/datasets/{id}/owner
   - Update owner_name, owner_contact
   - Re-score dataset (ownership dimension changes)
2. Implement POST /api/datasets/{id}/metadata
   - Update intended_use, limitations, display_name
   - Re-score dataset (operational dimension changes)
3. Test: Update metadata, verify score updates

### Demo Command:
```bash
curl -X POST http://localhost:8000/api/datasets/{id}/owner \
  -H "Content-Type: application/json" \
  -d '{"owner_name": "Data Team", "owner_contact": "#data-team"}'
curl http://localhost:8000/api/datasets/{id}
# Verify ownership score increased
```

---

## Milestone 8: Frontend Setup & Project Structure
**Goal:** Next.js app running with basic routing  
**Demo:** Navigate to localhost:3000, see placeholder pages

### Files to Create:
```
frontend/
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js (or use CSS modules)
├── .env.local.example
├── app/
│   ├── layout.tsx
│   ├── page.tsx (home/redirect)
│   ├── datasets/
│   │   ├── page.tsx (list page)
│   │   └── [id]/
│   │       └── page.tsx (detail page)
│   └── api/
│       └── client.ts (API client utilities)
└── components/
    ├── ui/ (basic components: Button, Card, etc.)
    └── datasets/ (dataset-specific components)
```

### Files to Modify:
- None (initial setup)

### Tasks:
1. Initialize Next.js 14+ project with TypeScript
2. Set up Tailwind CSS (or preferred styling)
3. Create basic layout with navigation
4. Set up API client to connect to backend
5. Create placeholder pages for /datasets and /datasets/[id]
6. Test: Start dev server, navigate pages

### Demo Command:
```bash
cd frontend && npm run dev
# Open http://localhost:3000/datasets
```

---

## Milestone 9: Dataset List Page
**Goal:** Display datasets with filtering  
**Demo:** See list of datasets, filter by status/owner, click to detail

### Files to Create:
```
frontend/
├── components/
│   ├── datasets/
│   │   ├── DatasetList.tsx
│   │   ├── DatasetCard.tsx
│   │   ├── DatasetFilters.tsx
│   │   └── ScoreBadge.tsx
└── app/
    └── datasets/
        └── page.tsx (implement list logic)
```

### Files to Modify:
```
frontend/
└── app/
    └── datasets/
        └── page.tsx (replace placeholder)
```

### Tasks:
1. Create DatasetList component with:
   - Table or card layout
   - Score badge with color coding
   - Status badge
   - Owner, display name
2. Add filtering UI (status dropdown, owner search, text search)
3. Connect to GET /api/datasets with query params
4. Add loading and error states
5. Link each dataset to detail page
6. Test: View datasets, apply filters

### Demo Command:
```bash
# Ensure backend running with mock data
# Open http://localhost:3000/datasets
# Filter by status, search by name
```

---

## Milestone 10: Dataset Detail Page - Score Display
**Goal:** Show score, status, dimension breakdown  
**Demo:** View dataset profile with score visualization

### Files to Create:
```
frontend/
├── components/
│   ├── datasets/
│   │   ├── DatasetHeader.tsx (score + status)
│   │   ├── DimensionBars.tsx (6 dimension scores)
│   │   └── ScoreHistory.tsx (sparkline)
└── app/
    └── datasets/
        └── [id]/
            └── page.tsx (implement detail page)
```

### Files to Modify:
```
frontend/
└── app/
    └── datasets/
        └── [id]/
            └── page.tsx (replace placeholder)
```

### Tasks:
1. Create DatasetHeader with:
   - Large score display (0-100)
   - Status badge
   - Display name, full name
2. Create DimensionBars component:
   - 6 bars, one per dimension
   - Show points awarded / max points
   - Color coding (green/yellow/red)
3. Fetch dataset detail from API
4. Display score history (simple line chart or sparkline)
5. Test: Navigate to dataset, see score breakdown

### Demo Command:
```bash
# Open http://localhost:3000/datasets/{id}
# See score, status, dimension bars
```

---

## Milestone 11: Dataset Detail Page - Reasons & Actions
**Goal:** Show why score is low and how to improve  
**Demo:** View reasons for point losses and actionable checklist

### Files to Create:
```
frontend/
├── components/
│   ├── datasets/
│   │   ├── ReasonsList.tsx (why score is low)
│   │   └── ActionsChecklist.tsx (improvement items)
```

### Files to Modify:
```
frontend/
└── app/
    └── datasets/
        └── [id]/
            └── page.tsx (add reasons and actions sections)
```

### Tasks:
1. Create ReasonsList component:
   - List all reasons with points lost
   - Group by dimension
   - Show reason_code and message
2. Create ActionsChecklist component:
   - List all actions with points gain
   - Show title, description, points_gain
   - Optional: mark as completed (local state)
3. Add sections to detail page
4. Test: View reasons and actions for different datasets

### Demo Command:
```bash
# Open http://localhost:3000/datasets/{id}
# Scroll to see reasons and actions
```

---

## Milestone 12: Dataset Metadata Editor
**Goal:** Edit owner, contact, intended use, limitations  
**Demo:** Update metadata, see score recalculate

### Files to Create:
```
frontend/
├── components/
│   ├── datasets/
│   │   ├── MetadataEditor.tsx
│   │   └── OwnerForm.tsx
└── hooks/
    └── useDataset.ts (data fetching + mutations)
```

### Files to Modify:
```
frontend/
└── app/
    └── datasets/
        └── [id]/
            └── page.tsx (add edit panel)
```

### Tasks:
1. Create MetadataEditor component with:
   - Form for intended_use, limitations, display_name
   - Submit button
   - Loading state
2. Create OwnerForm component:
   - Form for owner_name, owner_contact
   - Submit button
3. Implement mutations using React Query or SWR
4. On successful update, refetch dataset (score should update)
5. Add optimistic updates for better UX
6. Test: Update metadata, verify score changes

### Demo Command:
```bash
# Open http://localhost:3000/datasets/{id}
# Edit owner, submit, see score increase
```

---

## Milestone 13: Polish & Error Handling
**Goal:** Production-ready MVP with error handling  
**Demo:** Handle errors gracefully, loading states, responsive design

### Files to Create:
```
frontend/
├── components/
│   ├── ui/
│   │   ├── ErrorBoundary.tsx
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorMessage.tsx
└── app/
    └── error.tsx (Next.js error page)
```

### Files to Modify:
```
backend/
├── app/
│   ├── api/
│   │   └── datasets.py (add error handling)
│   └── main.py (add global exception handler)
frontend/
└── (all components - add loading/error states)
```

### Tasks:
1. Add error handling to all API endpoints
2. Create error boundary for frontend
3. Add loading states to all async operations
4. Improve responsive design (mobile-friendly)
5. Add form validation
6. Test: Trigger errors, verify graceful handling

### Demo Command:
```bash
# Test error cases:
# - Invalid dataset ID
# - Network errors
# - Validation errors
```

---

## Milestone 14: Testing & Documentation
**Goal:** Test coverage and API documentation  
**Demo:** Run test suite, view OpenAPI docs

### Files to Create:
```
backend/
├── tests/
│   ├── test_api.py
│   └── conftest.py (pytest fixtures)
└── docs/
    └── API.md (optional manual docs)
```

### Files to Modify:
```
backend/
└── app/
    └── main.py (ensure OpenAPI tags/descriptions)
```

### Tasks:
1. Write API integration tests:
   - Test dataset CRUD
   - Test scoring integration
   - Test metadata updates
2. Ensure scoring engine has unit tests
3. Verify OpenAPI docs are complete
4. Add README with setup instructions
5. Test: Run full test suite, view /docs endpoint

### Demo Command:
```bash
cd backend && pytest -v
# Open http://localhost:8000/docs
```

---

## Summary

### Backend Files (14 new files, 3 modified):
- Models, migrations, API routes, scoring engine, services, tests

### Frontend Files (15+ new files, 3 modified):
- Next.js app, components, pages, API client, hooks

### Key Milestones:
1. **M1-M2:** Infrastructure (DB + API server)
2. **M3:** Core scoring logic (testable)
3. **M4-M5:** Dataset API + scoring integration
4. **M6:** Demo data
5. **M7:** Metadata updates
6. **M8-M12:** Frontend (list → detail → editing)
7. **M13-M14:** Polish + testing

Each milestone produces a runnable demo that can be shown to stakeholders.


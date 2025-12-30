# Database Setup Guide

This guide covers the database schema, migrations, and seeding for Ondo MVP.

## Schema Overview

The MVP includes 5 tables:

### 1. `datasets`
Main dataset table storing core metadata and scores.
- **Primary Key**: `id` (UUID)
- **Unique Constraint**: `full_name`
- **Indexes**: 
  - `full_name` (unique)
  - `readiness_score`
  - `readiness_status`
  - Composite: `(readiness_status, readiness_score)`
  - `owner_name`

### 2. `dataset_dimension_scores`
Stores per-dimension scores for each dataset.
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `dataset_id` → `datasets.id` (CASCADE delete)
- **Unique Constraint**: `(dataset_id, dimension_key)`
- **Indexes**: 
  - `dataset_id`
  - `dimension_key`
  - Composite: `(dataset_id, dimension_key)`

### 3. `dataset_reasons`
Stores reasons for point losses in scoring.
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `dataset_id` → `datasets.id` (CASCADE delete)
- **Indexes**: 
  - `dataset_id`
  - `dimension_key`
  - `reason_code`
  - Composite: `(dataset_id, dimension_key)`

### 4. `dataset_actions`
Stores recommended actions to improve scores.
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `dataset_id` → `datasets.id` (CASCADE delete)
- **Indexes**: 
  - `dataset_id`
  - `action_key`
  - Composite: `(dataset_id, action_key)`

### 5. `dataset_score_history`
Historical record of dataset scores over time.
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `dataset_id` → `datasets.id` (CASCADE delete)
- **Indexes**: 
  - `dataset_id`
  - `readiness_score`
  - `recorded_at`
  - Composite: `(dataset_id, recorded_at)`

## Enums

Two PostgreSQL enums are created:

1. **`readiness_status_enum`**: `'draft' | 'internal' | 'production_ready' | 'gold'`
2. **`dimension_key_enum`**: `'ownership' | 'documentation' | 'schema_hygiene' | 'data_quality' | 'stability' | 'operational'`

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Create a `.env` file:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/ondo
DEBUG=false
```

### 3. Create Database

```bash
createdb ondo
# Or using psql:
# psql -c "CREATE DATABASE ondo;"
```

### 4. Run Migrations

```bash
alembic upgrade head
```

This will create all tables, indexes, and constraints.

### 5. Seed Demo Data (Optional)

```bash
python scripts/seed_demo_data.py
```

This creates 5 sample datasets with varied scores:
- `analytics.users` - High score (Gold status)
- `analytics.events` - Medium score (Production-Ready)
- `staging.raw_logs` - Low score (Draft)
- `analytics.revenue` - High score (Gold status)
- `experiments.ab_test_results` - Medium score (Internal)

## Migration Commands

### Create a new migration
```bash
alembic revision --autogenerate -m "description"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback one migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

### View current revision
```bash
alembic current
```

## SQLAlchemy Models

All models are defined in `app/models.py`:

- `Dataset` - Main dataset model
- `DatasetDimensionScore` - Dimension scores
- `DatasetReason` - Point loss reasons
- `DatasetAction` - Improvement actions
- `DatasetScoreHistory` - Score history

Models use SQLAlchemy 2.0 style with:
- Declarative base
- Relationship definitions
- Cascade deletes
- Proper indexing

## Database Session

Use `app.db.get_db()` for FastAPI dependency injection:

```python
from app.db import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

@app.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).all()
```

## Constraints and Indexes

All foreign keys use `ON DELETE CASCADE` to maintain referential integrity.

Indexes are optimized for common query patterns:
- Filtering by status and score
- Looking up by owner
- Querying dimension scores
- Retrieving score history


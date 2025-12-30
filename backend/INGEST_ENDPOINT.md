# Mock Ingestion Endpoint

## Overview

The `POST /api/ingest/mock` endpoint creates 10 realistic datasets with varying readiness attributes, scores them, and records all results in the database.

## Endpoint

**POST** `/api/ingest/mock`

## Description

This endpoint:
1. Creates or updates 10 realistic datasets
2. Scores each dataset using the scoring engine
3. Saves dimension scores, reasons, and actions
4. Records score history for each dataset
5. Returns a summary of ingested datasets

## Request

No request body required.

**Example:**
```bash
curl -X POST http://localhost:8000/api/ingest/mock
```

## Response

```json
{
  "ingested": 10,
  "errors": 0,
  "datasets": [
    {
      "id": "uuid",
      "full_name": "analytics.users",
      "display_name": "Users Table",
      "readiness_score": 85,
      "readiness_status": "gold"
    },
    ...
  ],
  "error_details": null
}
```

## Datasets Created

The endpoint creates 10 datasets with varied readiness scores:

1. **analytics.users** - High score (Gold)
   - Complete ownership, documentation, quality checks
   - All dimensions well-scored

2. **analytics.events** - Medium score (Production-Ready)
   - Missing some quality checks
   - Some breaking changes

3. **staging.raw_logs** - Low score (Draft)
   - Missing owner and description
   - Legacy columns present

4. **analytics.revenue** - High score (Gold)
   - Finance team ownership
   - Good documentation and quality checks

5. **experiments.ab_test_results** - Medium score (Internal)
   - Missing some column descriptions
   - No quality checks

6. **analytics.page_views** - High score (Production-Ready/Gold)
   - Product analytics ownership
   - Good documentation

7. **warehouse.inventory** - Medium-High score (Production-Ready)
   - Operations ownership
   - Good quality checks

8. **marketing.campaigns** - Low-Medium score (Draft/Internal)
   - Missing owner
   - Missing some documentation

9. **analytics.conversions** - High score (Gold)
   - Growth team ownership
   - Complete quality setup

10. **legacy.old_transactions** - Low score (Draft)
    - Legacy system
    - Missing quality checks
    - Legacy columns

## Scoring Details

Each dataset is scored using the full scoring engine, which evaluates:
- Ownership & Accountability (15 pts)
- Documentation Quality (20 pts)
- Schema Hygiene (15 pts)
- Data Quality Signals (20 pts)
- Stability & Change Management (20 pts)
- Operational Metadata (10 pts)

## Database Records Created

For each dataset, the following records are created:
- Dataset record with score and status
- 6 dimension score records (one per dimension)
- Reason records (for point losses)
- Action records (for improvements)
- Score history entry

## Idempotency

The endpoint is idempotent - running it multiple times will update existing datasets rather than creating duplicates. Datasets are matched by `full_name`.

## Usage

```bash
# Ingest mock data
curl -X POST http://localhost:8000/api/ingest/mock

# Verify datasets were created
curl http://localhost:8000/api/datasets

# Check a specific dataset
curl http://localhost:8000/api/datasets/{id}
```

## Testing

The endpoint is tested in `tests/test_api.py`:
- `test_ingest_mock_data` - Verifies ingestion and scoring
- `test_ingest_mock_data_idempotent` - Verifies idempotency


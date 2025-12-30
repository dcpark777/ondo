# Ondo Scoring Engine

Deterministic readiness scoring engine for datasets. This is a pure function implementation that takes dataset metadata and returns a complete scoring result.

## Usage

```python
from app.scoring.engine import score_dataset

metadata = {
    "owner_name": "Data Team",
    "owner_contact": "#data-team",
    "description": "User events table",
    "columns": [
        {"name": "user_id", "description": "User identifier"},
        {"name": "event_type", "description": "Event type"},
    ],
    "intended_use": "Analytics",
    "limitations": "Data delayed by 1 hour",
    "has_freshness_checks": True,
    "has_sla": True,
}

result = score_dataset(metadata)
print(f"Score: {result.total_score}/100")
print(f"Status: {result.status.value}")
```

## Scoring Dimensions

The engine evaluates 6 dimensions (100 points total):

1. **Ownership & Accountability** (15 pts)
   - +10 owner present
   - +5 escalation/contact present

2. **Documentation Quality** (20 pts)
   - +5 dataset description present
   - +10 >=80% columns documented

3. **Schema Hygiene** (15 pts)
   - +5 naming conventions pass (snake_case)
   - +5 nullable ratio under threshold
   - +5 no legacy/unused columns

4. **Data Quality Signals** (20 pts)
   - +10 freshness/volume checks exist
   - +5 SLA defined
   - +5 no unresolved failures (if measured)

5. **Stability & Change Management** (20 pts)
   - +10 no breaking changes in last 30 days (if measured)
   - +5 changes documented/versioned
   - +5 backward compatibility respected (if measured)

6. **Operational Metadata** (10 pts)
   - +5 intended use cases defined
   - +5 known limitations defined

## Status Mapping

- **0-49**: Draft
- **50-69**: Internal
- **70-84**: Production-Ready
- **85-100**: Gold

## Result Structure

`ScoreResult` contains:
- `total_score`: int (0-100)
- `status`: ReadinessStatus enum
- `dimension_scores`: List of DimensionScore objects
- `reasons`: List of Reason objects (point losses with explanations)
- `actions`: List of Action objects (recommendations with point gains)

## Testing

Run the test suite:
```bash
pytest tests/test_scoring.py -v
```

The test suite includes 8 scenarios covering:
- Perfect Gold dataset
- Minimal Draft dataset
- Partial ownership
- Production-Ready with gaps
- Schema hygiene issues
- Documentation coverage
- Internal status
- Data quality signals

## Design Principles

1. **Deterministic**: Same metadata always produces the same score
2. **Transparent**: Every point loss has a clear reason
3. **Fair**: Missing optional fields don't cause penalties
4. **Actionable**: Every issue has a recommended action with point gain


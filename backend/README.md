# Ondo Backend

Backend API for Ondo dataset readiness scoring.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure database:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Seed demo data (optional):**
   ```bash
   python scripts/seed_demo_data.py
   ```

## Project Structure

```
backend/
├── app/
│   ├── models.py          # SQLAlchemy models
│   ├── db.py              # Database session management
│   ├── config.py          # Configuration
│   └── scoring/           # Scoring engine
├── alembic/               # Database migrations
├── scripts/               # Utility scripts
└── tests/                 # Test suite
```

## Database Models

- `Dataset` - Main dataset table
- `DatasetDimensionScore` - Per-dimension scores
- `DatasetReason` - Point loss reasons
- `DatasetAction` - Improvement recommendations
- `DatasetScoreHistory` - Historical score tracking

## Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```


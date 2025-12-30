# Ondo

Dataset readiness scoring SaaS - Score datasets for data product readiness and get actionable improvements.

## Quick Start

### Docker/Podman (Recommended) 🐳

The easiest way to run everything (automatically uses Podman if available, otherwise Docker):

```bash
# Start all services
docker-compose up

# Or in background
docker-compose up -d

# Demo data seeds automatically on first startup!
# To manually re-seed:
docker-compose exec backend python scripts/seed_demo_data.py
# Or use the API
curl -X POST http://localhost:8000/api/ingest/mock
```

Visit http://localhost:3000 to see the application.

**Using Make (recommended):**
```bash
make up      # Start services (auto-seeds demo data on first startup)
make logs    # View logs
make down    # Stop services
make help    # See all commands
```

**Quick Start Sequence:**
```bash
make up      # Start all services (demo data seeds automatically)
# Wait ~30 seconds for startup, then visit http://localhost:3000
```

**Note:** Demo data is automatically seeded on first startup. To manually re-seed:
```bash
make seed        # Only seeds if database is empty
make seed-force  # Clears existing data and re-seeds
```

See [DOCKER.md](./DOCKER.md) for complete Docker documentation.

### Manual Setup

See [QUICKSTART.md](./QUICKSTART.md) for complete setup instructions.

```bash
# Backend
cd backend
pip install -r requirements.txt
createdb ondo
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## Features

- **Deterministic Scoring**: Transparent 0-100 readiness score
- **6 Dimensions**: Ownership, Documentation, Schema Hygiene, Data Quality, Stability, Operational
- **Actionable Insights**: Every point loss includes a reason and remediation action
- **Score History**: Track score changes over time
- **AI Assist** (optional): Generate dataset descriptions with AI

## Project Structure

- `backend/` - FastAPI backend with scoring engine
- `frontend/` - Next.js frontend with React
- `BUILD_PLAN.md` - Complete build plan with milestones
- `QUICKSTART.md` - Setup and run instructions

## Documentation

- [Quick Start Guide](./QUICKSTART.md) - How to run the app
- [Build Plan](./BUILD_PLAN.md) - Development milestones
- [Code Quality](./backend/CODE_QUALITY.md) - Coding standards
- [API Documentation](./backend/API_DOCUMENTATION.md) - API reference

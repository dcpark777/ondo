# Ondo Quick Start Guide

Complete guide to set up and run the Ondo dataset readiness scoring application.

## Quickest Start: Docker Compose

The easiest way to run the entire application:

```bash
# Start everything (database, backend, frontend)
docker-compose up

# Or in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

To seed demo data:
```bash
docker-compose exec backend python scripts/seed_demo_data.py
# Or
curl -X POST http://localhost:8000/api/ingest/mock
```

## Manual Setup (Alternative)

### Prerequisites

- Python 3.11+ (for backend)
- Node.js 18+ and npm (for frontend)
- PostgreSQL 12+ (for database)

## Backend Setup

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or using a virtual environment (recommended):

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Database

Create a `.env` file in the `backend` directory:

```bash
cd backend
cp .env.example .env  # If .env.example exists, or create manually
```

Edit `.env` with your database credentials:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ondo
DEBUG=false
AI_ASSIST_ENABLED=false  # Set to true to enable AI assist
```

### 3. Create Database

```bash
# Using psql
psql -U postgres -c "CREATE DATABASE ondo;"

# Or using createdb
createdb ondo
```

### 4. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

This creates all tables, indexes, and constraints.

### 5. (Optional) Seed Demo Data

```bash
cd backend
python scripts/seed_demo_data.py
```

Or use the API endpoint:

```bash
curl -X POST http://localhost:8000/api/ingest/mock
```

### 6. Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create a `.env.local` file:

```bash
cd frontend
cp .env.local.example .env.local
```

Edit `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at:
- http://localhost:3000

## Full Application Flow

### 1. Start Backend

```bash
# Terminal 1
cd backend
source venv/bin/activate  # If using venv
uvicorn app.main:app --reload
```

### 2. Start Frontend

```bash
# Terminal 2
cd frontend
npm run dev
```

### 3. Access Application

Open your browser:
- Frontend: http://localhost:3000
- Backend API Docs: http://localhost:8000/docs

### 4. Ingest Demo Data

If you haven't seeded data yet:

```bash
# Option 1: Using the seed script
cd backend
python scripts/seed_demo_data.py

# Option 2: Using the API
curl -X POST http://localhost:8000/api/ingest/mock
```

### 5. View Datasets

Navigate to http://localhost:3000/datasets to see the dataset list.

## Common Commands

### Backend

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_scoring.py -v

# Check API health
curl http://localhost:8000/health
```

### Frontend

```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint
npm run lint
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Verify database exists
psql -U postgres -l | grep ondo

# Test connection
psql postgresql://postgres:postgres@localhost:5432/ondo
```

### Port Already in Use

```bash
# Backend (default: 8000)
uvicorn app.main:app --reload --port 8001

# Frontend (default: 3000)
npm run dev -- -p 3001
```

### Migration Issues

```bash
# Reset database (WARNING: deletes all data)
dropdb ondo
createdb ondo
alembic upgrade head
```

### Python Import Errors

```bash
# Ensure you're in the backend directory
cd backend

# Verify virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt
```

## Production Deployment

### Backend

```bash
# Use production ASGI server
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Or with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
# Build static files
npm run build

# Serve with Next.js
npm start

# Or export static files
npm run build
# Serve the 'out' directory with any static file server
```

## Environment Variables

### Backend (.env)

```bash
DATABASE_URL=postgresql://user:password@host:port/database
DEBUG=false
AI_ASSIST_ENABLED=false
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **View Datasets**: Navigate to http://localhost:3000/datasets
3. **Test Scoring**: Update dataset metadata and watch scores change
4. **Try AI Assist**: Enable `AI_ASSIST_ENABLED=true` and use AI suggestions

## Project Structure

```
ondo/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── scoring/      # Scoring engine
│   │   ├── services/     # Business logic
│   │   └── models.py     # Database models
│   ├── alembic/          # Database migrations
│   ├── tests/            # Test suite
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── app/              # Next.js app directory
│   │   ├── datasets/     # Dataset pages
│   │   └── api/          # API client
│   └── package.json      # Node dependencies
└── README.md
```

## Support

For issues or questions:
- Check the API docs at http://localhost:8000/docs
- Review `CODE_QUALITY.md` for coding standards
- See `BUILD_PLAN.md` for architecture details


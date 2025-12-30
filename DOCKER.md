# Container Setup Guide

Complete guide to running Ondo with Docker/Podman and Docker Compose.

**Note:** The Makefile automatically detects and uses Podman if available, otherwise falls back to Docker.

## Quick Start

```bash
# Start all services
docker-compose up

# Or in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Services

The `docker-compose.yml` includes:

1. **PostgreSQL Database** (`db`)
   - Port: 5432
   - Database: `ondo`
   - User: `postgres` / Password: `postgres`
   - Data persisted in volume: `postgres_data`

2. **Backend API** (`backend`)
   - Port: 8000
   - Runs migrations on startup
   - Auto-reloads in development mode

3. **Frontend** (`frontend`)
   - Port: 3000
   - Connects to backend at `http://localhost:8000`

## Development Mode

For development with hot-reload:

```bash
# Use development override
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This enables:
- Hot-reload for backend (code changes auto-restart)
- Hot-reload for frontend (Next.js dev server)
- Volume mounts for live code editing

## Environment Variables

### Backend

Set in `docker-compose.yml` or create `.env` file:

```yaml
environment:
  DATABASE_URL: postgresql://postgres:postgres@db:5432/ondo
  DEBUG: "false"
  AI_ASSIST_ENABLED: "false"
```

### Frontend

Set in `docker-compose.yml`:

```yaml
environment:
  NEXT_PUBLIC_API_URL: http://localhost:8000
```

## Common Commands

### Start Services

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Start specific service
docker-compose up backend
```

### Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (clean database)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Execute Commands

```bash
# Run migrations manually
docker-compose exec backend alembic upgrade head

# Seed demo data
docker-compose exec backend python scripts/seed_demo_data.py

# Access database
docker-compose exec db psql -U postgres -d ondo

# Run backend shell
docker-compose exec backend python

# Run tests
docker-compose exec backend pytest tests/ -v
```

### Rebuild Services

```bash
# Rebuild all
docker-compose build

# Rebuild specific service
docker-compose build backend

# Rebuild without cache
docker-compose build --no-cache
```

## Seeding Data

After starting services, seed demo data:

```bash
# Option 1: Using seed script
docker-compose exec backend python scripts/seed_demo_data.py

# Option 2: Using API endpoint
curl -X POST http://localhost:8000/api/ingest/mock
```

## Troubleshooting

### Port Already in Use

If ports 3000, 8000, or 5432 are in use:

```yaml
# Edit docker-compose.yml to change ports
ports:
  - "3001:3000"  # Frontend on 3001
  - "8001:8000"  # Backend on 8001
  - "5433:5432"  # Database on 5433
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec backend python -c "from app.db import engine; engine.connect()"
```

### Backend Not Starting

```bash
# Check backend logs
docker-compose logs backend

# Check if migrations ran
docker-compose exec backend alembic current

# Run migrations manually
docker-compose exec backend alembic upgrade head
```

### Frontend Build Issues

```bash
# Rebuild frontend
docker-compose build --no-cache frontend

# Check frontend logs
docker-compose logs frontend
```

### Clean Slate

```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose rm -f

# Start fresh
docker-compose up --build
```

## Production Deployment

For production, use the production Dockerfiles:

```bash
# Build production images
docker-compose -f docker-compose.yml build

# Run in production mode
docker-compose up -d
```

Production optimizations:
- Multi-stage builds for smaller images
- No development dependencies
- Optimized Next.js build
- Health checks enabled

## Dockerfile Details

### Backend Dockerfile

- Base: Python 3.11-slim
- Installs PostgreSQL client for migrations
- Runs migrations on startup
- Exposes port 8000

### Frontend Dockerfile

- Multi-stage build:
  - `deps`: Install dependencies
  - `builder`: Build Next.js app
  - `runner`: Production image
- Uses Next.js standalone output
- Runs as non-root user

## Health Checks

All services include health checks:

- **Database**: `pg_isready`
- **Backend**: HTTP GET `/health`
- **Frontend**: HTTP GET on port 3000

Services wait for dependencies to be healthy before starting.

## Volumes

- `postgres_data`: Persistent database storage
- Development mode mounts source code for hot-reload

## Network

All services are on the default Docker network and can communicate by service name:
- Backend connects to database at `db:5432`
- Frontend connects to backend at `backend:8000` (internal)


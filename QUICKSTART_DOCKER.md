# Docker Quick Start

The fastest way to get Ondo running.

## One-Command Start (with demo data)

```bash
# Start services and seed data
docker-compose up -d && sleep 30 && docker-compose exec backend python scripts/seed_demo_data.py
```

## Step-by-Step

### 1. Start Services

```bash
docker-compose up -d
```

Wait about 30 seconds for all services to start and become healthy.

### 2. Seed Demo Data

You have two options:

**Option A: Using the seed script**
```bash
docker-compose exec backend python scripts/seed_demo_data.py
```

**Option B: Using the API endpoint**
```bash
curl -X POST http://localhost:8000/api/ingest/mock
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Using Make Commands

```bash
# Start services
make up

# Wait ~30 seconds for services to be ready, then:
make seed

# View logs
make logs

# Stop services
make down
```

## Verify Everything Works

```bash
# Check services are running
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# List datasets (should show 10 after seeding)
curl http://localhost:8000/api/datasets
```

## Troubleshooting

**Services won't start?**
```bash
# Check logs
docker-compose logs

# Restart
docker-compose restart
```

**No data after seeding?**
```bash
# Check if seed script ran successfully
docker-compose logs backend | grep -i seed

# Try seeding again
make seed
```

**Port conflicts?**
Edit `docker-compose.yml` to change ports:
- Frontend: `3000:3000` → `3001:3000`
- Backend: `8000:8000` → `8001:8000`
- Database: `5432:5432` → `5433:5432`


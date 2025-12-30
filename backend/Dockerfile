FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Wait for database and run migrations, then seed data (if empty), then start server
CMD ["sh", "-c", "until pg_isready -h db -p 5432 -U postgres; do sleep 2; done && alembic upgrade head && python scripts/seed_demo_data.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]


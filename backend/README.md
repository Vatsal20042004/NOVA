# E-Commerce Backend

FastAPI-based e-commerce API with PostgreSQL, Redis, and Celery. See [ARCHITECTURE.md](../ARCHITECTURE.md) and [ALGORITHMS.md](../ALGORITHMS.md) in the repo root for design and algorithm details.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or SQLite for local dev)
- Redis 7+
- (Optional) Node.js 20+ for frontend

## Setup

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Unix: source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env: DATABASE_URL, REDIS_URL, JWT_SECRET_KEY
```

## Database

```bash
# Migrations (PostgreSQL or SQLite)
alembic upgrade head
```

## Run

```bash
# API server
uvicorn app.main:app --reload

# Celery worker (separate terminal)
celery -A app.workers.celery_app worker -l info

# Celery Beat for scheduled tasks (optional)
celery -A app.workers.celery_app beat -l info
```

## Test

```bash
pytest --cov=app
```

## Environment

| Variable | Description |
|----------|-------------|
| DATABASE_URL | PostgreSQL or SQLite URL |
| REDIS_URL | Redis connection URL |
| JWT_SECRET_KEY | Secret for JWT signing |
| CELERY_BROKER_URL | Redis broker for Celery |

See [.env.example](.env.example) for full list.

## API

- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## Backend-only (no frontend)

From repo root:

```bash
docker-compose up -d db redis backend
# Optional: celery worker
docker-compose run --rm backend celery -A app.workers.celery_app worker -l info
```

Then use the API at http://localhost:8000.

# Deployment Guide

This guide describes how to deploy the Delivery System application.

## Prerequisites

- Docker and Docker Compose installed
- Git installed

## Configuration

1. **Environment Variables**:
   Ensure `.env` file exists in `backend/` directory with production settings.
   Example:
   ```
   DATABASE_URL=postgresql://user:password@db:5432/delivery
   SECRET_KEY=your_production_secret_key
   ...
   ```

2. **Docker Compose**:
   The `docker-compose.prod.yml` file defines the production services:
   - `db`: PostgreSQL database
   - `backend`: FastAPI application
   - `frontend`: React application served via Nginx

## Deployment Steps

1. **Build and Run**:
   Execute the following command in the root directory:
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

2. **Verify Services**:
   Check if containers are running:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

3. **Database Migrations**:
   The backend container should automatically run migrations on startup (if configured in `start.sh` or equivalent).
   If not, you can run manually:
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

4. **Access the Application**:
   - Frontend: http://localhost (or your server IP)
   - Backend API: http://localhost/api/v1/
   - API Docs: http://localhost/api/v1/docs

## Testing

The application has a comprehensive test suite.
To run tests locally (requires local Python environment):
```bash
cd backend
python -m pytest tests/
```

## Troubleshooting

- **Logs**:
  View logs for a service:
  ```bash
  docker-compose -f docker-compose.prod.yml logs -f backend
  ```

- **Rebuild**:
  Force a rebuild of images:
  ```bash
  docker-compose -f docker-compose.prod.yml up --build --force-recreate -d
  ```

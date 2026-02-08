"""
FastAPI Application Entry Point
Production-grade e-commerce platform backend
"""

import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.core.config import settings
from app.core.cache import cache
from app.core.exceptions import AppException
from app.api.v1.router import api_router
from app.db.session import engine
from app.db.base import Base
# Import all models to register them with Base
from app.models import User, Product, Category, Order, OrderItem, Payment, Review, Inventory

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Prometheus metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)


def _normalize_path(path: str) -> str:
    """Replace numeric IDs in path to reduce metric cardinality."""
    return re.sub(r"/\d+", "/:id", path) if path else "/"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting application...")
    
    # Create tables for SQLite (dev mode)
    if settings.is_sqlite:
        logger.info("Using SQLite database - creating tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    # Connect to Redis (optional)
    try:
        await cache.connect()
        if cache.is_connected:
            logger.info("Redis connected")
        else:
            logger.info("Redis not available - running without cache")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e} - running without cache")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Disconnect from Redis
    try:
        await cache.disconnect()
        logger.info("Redis disconnected")
    except Exception as e:
        logger.warning(f"Redis disconnect error: {e}")
    
    # Dispose database engine
    await engine.dispose()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## E-Commerce Platform API
    
    A production-grade, scalable e-commerce backend system.
    
    ### Features
    - **Authentication**: JWT-based auth with refresh tokens
    - **Products**: Full CRUD with search, filtering, and ranking
    - **Orders**: Transactional order processing with inventory management
    - **Payments**: Simulated payment processing with retry logic
    - **Recommendations**: Co-occurrence based product recommendations
    
    ### Architecture
    - Service-oriented design with 6 logical services
    - PostgreSQL with async SQLAlchemy
    - Redis for caching and distributed locking
    - Celery/BackgroundTasks for async processing
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# ==================== Middleware ====================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next: Callable):
    """
    Middleware for request logging and tracking.
    Adds request ID and timing information.
    """
    # Generate or get request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # Add to request state
    request.state.request_id = request_id
    
    # Start timing
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    norm_path = _normalize_path(request.url.path)
    
    # Prometheus metrics
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        path=norm_path,
        status=response.status_code,
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        path=norm_path,
    ).observe(duration)
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.4f}"
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.4f}s - "
        f"Request-ID: {request_id}"
    )
    
    return response


# ==================== Exception Handlers ====================

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application-specific exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    # Convert errors to JSON-safe format (ValueError objects aren't serializable)
    errors = []
    for error in exc.errors():
        safe_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": str(error.get("input")) if error.get("input") is not None else None,
        }
        errors.append(safe_error)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error",
            "details": errors,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# ==================== Routes ====================

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns status of database and Redis connections.
    """
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Check database
    try:
        from sqlalchemy import text
        from app.db.session import async_session_maker
        
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis (optional: cache, locks, rate limiting degrade without it)
    if cache.is_connected:
        try:
            await cache.client.ping()
            health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
    else:
        health_status["redis"] = "disconnected (optional)"
    
    status_code = (
        status.HTTP_200_OK 
        if health_status["status"] == "healthy" 
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/metrics", tags=["Metrics"])
async def metrics():
    """
    Prometheus metrics endpoint.
    Exposes http_requests_total and http_request_duration_seconds.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ==================== Run Configuration ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4
    )

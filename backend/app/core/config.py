"""
Application Configuration
Uses Pydantic Settings for environment variable management
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "E-Commerce Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]
    
    # Database (SQLite for easy local dev, PostgreSQL for production)
    DATABASE_URL: str = "sqlite+aiosqlite:///./ecommerce.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Email (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@ecommerce.com"
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite"""
        return "sqlite" in self.DATABASE_URL
    
    @property
    def async_database_url(self) -> str:
        """Ensure database URL uses asyncpg driver"""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return self.DATABASE_URL
    
    @property
    def sync_database_url(self) -> str:
        """Get sync database URL for Alembic"""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()

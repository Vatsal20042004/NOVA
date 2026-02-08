# Test configuration
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings


# Test database URL
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "/ecommerce", "/ecommerce_test"
)


# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

# Create test session maker
test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    Uses transaction rollback for test isolation.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session with transaction
    async with test_session_maker() as session:
        yield session
        await session.rollback()
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with overridden dependencies.
    """
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_db] = override_get_session
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def test_product_data():
    """Sample product data for testing."""
    return {
        "name": "Test Product",
        "description": "A test product for testing",
        "price": 99.99,
        "slug": "test-product-001"
    }


@pytest.fixture
def test_category_data():
    """Sample category data for testing."""
    return {
        "name": "Test Category",
        "description": "A test category",
        "slug": "test-category"
    }

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db.base import Base
from app.core.db.session import get_db
from app.main import app


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    TestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSession() as s:
        yield s
        await s.rollback()


@pytest.fixture
def mock_redis() -> MagicMock:
    r = MagicMock()
    pipe = MagicMock()
    pipe.execute.return_value = [0, 1, 1, True]
    r.pipeline.return_value = pipe
    return r


@pytest_asyncio.fixture
async def client(session: AsyncSession, mock_redis: MagicMock) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    app.state.get_redis = lambda: mock_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    if hasattr(app.state, "get_redis"):
        del app.state.get_redis


@pytest.fixture
def booking_payload() -> dict:
    return {
        "name": "Ivan Lodygin",
        "datetime": datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc).isoformat(),
        "service_type": "consultation",
    }

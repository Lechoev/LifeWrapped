import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.conf.base import Base
from src.conf.uow import UnitOfWork
from src.main import app

DATABASE_URL_TEST = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL_TEST, poolclass=NullPool)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
def mock_cache():
    mock = AsyncMock()
    mock.set = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.exists = AsyncMock(return_value=False)
    mock.set_if_not_exists = AsyncMock(return_value=True)
    mock.delete = AsyncMock()
    mock.close = AsyncMock()
    return mock


@pytest.fixture(autouse=True)
def setup_all_mocks(mock_cache):
    mock_sync_cache = MagicMock()
    mock_sync_cache.set_if_not_exists = MagicMock(return_value=True)

    mock_celery_task = MagicMock()
    mock_celery_task.delay = MagicMock()

    patches = []

    patches.append(
        patch(
            "src.auth_user.emails.factory.get_async_redis_cache",
            return_value=mock_cache,
        )
    )
    patches.append(
        patch(
            "src.auth_user.emails.factory.get_redis_cache", return_value=mock_sync_cache
        )
    )
    patches.append(
        patch(
            "src.auth_user.dependencies.get_async_redis_cache", return_value=mock_cache
        )
    )
    patches.append(patch("redis.asyncio.from_url", return_value=mock_cache))
    patches.append(patch("redis.from_url", return_value=mock_sync_cache))
    patches.append(patch("src.auth_user.services.send_email", mock_celery_task))
    patches.append(patch("src.auth_user.tasks.send_email", mock_celery_task))
    patches.append(patch("src.auth_user.emails.redis_cache.AsyncRedisCache.__new__"))
    patches.append(patch("redis.Redis", MagicMock()))
    patches.append(patch("redis.asyncio.Redis", AsyncMock()))
    patches.append(patch("kombu.Connection", MagicMock()))
    patches.append(patch("celery.Celery", MagicMock()))

    started_patches = []
    for p in patches:
        try:
            started_patches.append(p.start())
        except AttributeError:
            continue

    yield

    for p in started_patches:
        try:
            p.stop()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def override_dependencies(async_session, mock_cache):
    import src.common.dependencies as deps

    orig_create_uow = deps.create_uow
    orig_get_uow_factory = deps.get_uow_factory

    def test_create_uow():
        return UnitOfWork(session_factory=lambda: async_session)

    def test_get_uow_factory():
        def factory():
            return test_create_uow()

        return factory

    deps.create_uow = test_create_uow
    deps.get_uow_factory = test_get_uow_factory

    app.dependency_overrides[orig_get_uow_factory] = test_get_uow_factory

    try:
        import src.auth_user.dependencies as auth_deps

        if hasattr(auth_deps, "get_uow_factory"):
            original_auth_uow = auth_deps.get_uow_factory
            auth_deps.get_uow_factory = test_get_uow_factory
            app.dependency_overrides[original_auth_uow] = test_get_uow_factory

        if hasattr(auth_deps, "get_auth_service"):
            original_get_auth_service = auth_deps.get_auth_service

            def test_get_auth_service():
                from src.auth_user.services import AuthService

                return AuthService(uow_factory=test_get_uow_factory(), cache=mock_cache)

            auth_deps.get_auth_service = test_get_auth_service
            app.dependency_overrides[original_get_auth_service] = test_get_auth_service

    except ImportError:
        pass

    yield

    deps.create_uow = orig_create_uow
    deps.get_uow_factory = orig_get_uow_factory

    try:
        import src.auth_user.dependencies as auth_deps

        if hasattr(auth_deps, "get_uow_factory") and "original_auth_uow" in locals():
            auth_deps.get_uow_factory = original_auth_uow
        if (
            hasattr(auth_deps, "get_auth_service")
            and "original_get_auth_service" in locals()
        ):
            auth_deps.get_auth_service = original_get_auth_service
    except ImportError:
        pass

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def uow_factory(async_session):
    def factory():
        return UnitOfWork(session_factory=lambda: async_session)

    return factory

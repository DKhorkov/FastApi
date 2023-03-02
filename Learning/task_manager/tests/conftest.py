import pytest
import asyncio

from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi.testclient import TestClient

from Learning.task_manager.database.database import get_async_session
from Learning.task_manager.main import task_manager

from .session_for_test import get_test_async_session, test_engine, TestBase
from .user_routes_for_test import test_user_router
from .db_routes_for_test import test_db_router


# Переписываем зависимость нашего клиента под тестовую сессию:
task_manager.dependency_overrides[get_async_session] = get_test_async_session
task_manager.include_router(test_user_router)
task_manager.include_router(test_db_router)


# SETUP. Обязательное условие для корректной работы pytest.
@pytest.fixture(scope='session')
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


test_client = TestClient(task_manager)


@pytest.fixture(autouse=True, scope='session')
async def prepare_database():
    """
        Создает тестовую БД и таблицы на старте автотестов и удаляет таблицы по их окончании.

        :return: None
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)


@pytest.fixture(scope="session")
async def get_test_async_client() -> AsyncGenerator[AsyncClient, None]:
    """
        Метод возвращает асинхронного клиента для тестирования асинхронных ендпоинтов.

        :return: Асинхронный тестовый клиент
    """
    async with AsyncClient(app=task_manager, base_url="http://test") as test_async_client:
        yield test_async_client

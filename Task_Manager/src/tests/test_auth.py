from httpx import AsyncClient
from sqlalchemy.future import select

from .conftest import TestBase
from .session_for_test import create_test_db_and_tables, get_test_async_session, TestToken, TestUser


# async def test_creating_tables():
#     await create_test_db_and_tables()
#     assert TestBase.metadata.tables.keys().__str__() == "dict_keys(['test_user', 'test_task', 'test_token'])"


async def test_register_user(get_test_async_client: AsyncClient):
    response = await get_test_async_client.post(
        "/test_process_register",
        data={
            'email': 'test_email@mail.ru',
            'username': 'test_user',
            'password': 'test_password'
        }
    )
    assert response.status_code == 303

    session = await get_test_async_session()
    all_users = await session.execute(select(TestUser))
    assert len(all_users.scalars().all()) == 1


async def test_register_same_user(get_test_async_client: AsyncClient):
    response = await get_test_async_client.post(
        "/test_process_register",
        data={
            'email': 'test_email@mail.ru',
            'username': 'test_user',
            'password': 'test_password'
        }
    )

    # Редирект обратно на поле регистрации:
    assert response.status_code == 200

    session = await get_test_async_session()
    all_users = await session.execute(select(TestUser))
    assert len(all_users.scalars().all()) == 1


async def test_login(get_test_async_client: AsyncClient):
    response = await get_test_async_client.post(
        "/test_auth",
        data={
            'username': 'test_email@mail.ru',
            'password': 'test_password'
        }
    )

    assert response.status_code == 303

    # После авторизации создался токен для юзера:
    session = await get_test_async_session()
    all_tokens = await session.execute(select(TestToken))
    assert len(all_tokens.scalars().all()) == 1


async def test_login_unregistered_user(get_test_async_client: AsyncClient):
    response = await get_test_async_client.post(
        "/test_auth",
        data={
            'username': 'test_email228@mail.ru',
            'password': 'test_password'
        }
    )

    # Редирект на страницу логина снова с уведомлением, что такой юзер не зарегистрирован:
    assert response.status_code == 200


async def test_login_with_invalid_password(get_test_async_client: AsyncClient):
    response = await get_test_async_client.post(
        "/test_auth",
        data={
            'username': 'test_email@mail.ru',
            'password': 'invalid_password'
        }
    )

    # Редирект на страницу логина снова с уведомлением, что пароль не валиден:
    assert response.status_code == 200


async def test_logout(get_test_async_client: AsyncClient):
    response = await get_test_async_client.get(
        "/test_logout"
    )

    assert response.status_code == 303


if __name__ == '__main__':
    # test_creating_tables()
    test_register_user(AsyncClient)
    test_register_same_user(AsyncClient)
    test_login(AsyncClient)
    test_login_unregistered_user(AsyncClient)
    test_login_with_invalid_password(AsyncClient)
    test_logout(AsyncClient)

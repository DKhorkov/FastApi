from httpx import AsyncClient
from sqlalchemy.future import select

from Task_Manager.src.users.models import RegisterUser
from .user_utils_for_test import get_user_by_email, get_user_by_token, create_user_token, \
    create_user
from .session_for_test import get_test_async_session, TestToken, TestUser


async def test_create_user(get_test_async_client: AsyncClient):

    test_user = RegisterUser(email='test_email@mail.ru', username='test_user', password='test_password')
    await create_user(user=test_user)

    session = await get_test_async_session()
    all_users = await session.execute(select(TestUser))
    assert len(all_users.scalars().all()) == 1


async def test_get_user_by_email(get_test_async_client: AsyncClient):
    test_user = await get_user_by_email('test_email@mail.ru')
    assert test_user.email == 'test_email@mail.ru'
    assert test_user.username == 'test_user'


async def test_create_token_and_get_user_by_token(get_test_async_client: AsyncClient):
    await create_user_token(user_id=1)

    session = await get_test_async_session()
    all_tokens = await session.execute(select(TestToken))
    assert len(all_tokens.scalars().all()) == 1

    token = await session.execute(select(TestToken).filter(TestToken.user_id == 1))
    token = token.scalar()

    user = await get_user_by_token(token.token)
    assert user.id == 1
    assert user.email == 'test_email@mail.ru'
    assert user.username == 'test_user'


if __name__ == '__main__':
    test_create_user(AsyncClient)
    test_get_user_by_email(AsyncClient)
    test_create_token_and_get_user_by_token(AsyncClient)

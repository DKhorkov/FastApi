import logging

from datetime import datetime, timedelta

from fastapi import HTTPException, status, Depends
from sqlalchemy.future import select

from Learning.task_manager.users.models import RegisterUser, TokenBase
from Learning.task_manager.users.utils import hash_password, get_random_string, OAuth2PasswordBearerWithCookie
from .session_for_test import get_test_async_session, TestUser, TestToken


logging.basicConfig(format='[%(asctime)s: %(levelname)s] %(message)s', filename='./log/test_logs', filemode='a')
logger = logging.getLogger("")
logger.setLevel(level=logging.DEBUG)

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="test_auth")


async def get_user_by_email(email: str) -> TestUser:
    """
        Возвращает информацию о пользователе.
    """
    try:
        session = await get_test_async_session()
        user = await session.execute(select(TestUser).filter(TestUser.email == email))
        user = user.scalar()
        return user

    except Exception as e:
        logger.debug(e)


async def get_user_by_token(token: str) -> TestUser:
    """
        Возвращает информацию о владельце указанного токена
    """
    try:
        session = await get_test_async_session()
        user = await session.execute(select(TestUser).join(TestToken, TestUser.id == TestToken.user_id).where(
            (TestToken.token == token) & (TestToken.expires > datetime.now())))
        user = user.scalar()
        return user

    except Exception as e:
        logger.debug(e)


async def create_user_token(user_id: int) -> TokenBase:
    """
        Создает токен для пользователя с указанным user_id.
    """
    try:
        new_token = TestToken(user_id=user_id, expires=datetime.now() + timedelta(weeks=2))
        session = await get_test_async_session()
        session.add(new_token)
        await session.commit()
        await session.refresh(new_token)
        return TokenBase(token=new_token.token, expires=new_token.expires)

    except Exception as e:
        logger.debug(e)


async def create_user(user: RegisterUser) -> None:
    """
        Создает нового пользователя в БД.
    """
    try:
        salt = get_random_string()
        hashed_password = hash_password(user.password, salt)

        new_user = TestUser(email=user.email, username=user.username, hashed_password=f"{salt}${hashed_password}")
        session = await get_test_async_session()
        session.add(new_user)
        await session.commit()

    except Exception as e:
        logger.debug(e)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TestUser:
    """
        Функция получает токен, определяет, какому пользователю в Бд принадлежит данный токен и, если есть такой
        пользователь и он является активным, возвращает данного пользователя.

        :param token: Токен, полученный из cookies, для определения текущего пользователя

        :return: Объект пользователя (модель User) из БД
    """
    try:
        user = await get_user_by_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )
        return user

    except Exception as e:
        logger.debug(e)

import hashlib
import random
import string

from datetime import datetime, timedelta

from typing import Optional, Dict

from fastapi import HTTPException
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.future import select
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from Learning.task_manager.database.database import Token, User, get_async_session
from .models import RegisterUser, TokenBase


def get_random_string(length=12):
    """ Генерирует случайную строку, использующуюся как соль """
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def hash_password(password: str, salt: str = None):
    """ Хеширует пароль с солью """
    if salt is None:
        salt = get_random_string()
    enc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return enc.hex()


def validate_password(password: str, hashed_password: str):
    """ Проверяет, что хеш пароля совпадает с хешем из БД """
    salt, hashed = hashed_password.split("$")
    return hash_password(password, salt) == hashed


async def get_user_by_email(email: str):
    """ Возвращает информацию о пользователе """
    session = await get_async_session()
    user = await session.execute(select(User).filter(User.email == email))
    user = user.scalar()

    return user


async def get_user_by_token(token: str):
    """ Возвращает информацию о владельце указанного токена """
    session = await get_async_session()
    user = await session.execute(select(User).join(Token, User.id == Token.user_id).where(
        (Token.token == token) & (Token.expires > datetime.now())))
    user = user.scalar()

    return user


async def create_user_token(user_id: int):
    """ Создает токен для пользователя с указанным user_id """
    new_token = Token(user_id=user_id, expires=datetime.now() + timedelta(weeks=2))
    session = await get_async_session()
    session.add(new_token)
    await session.commit()
    await session.refresh(new_token)

    return TokenBase(token=new_token.token, expires=new_token.expires)


async def create_user(user: RegisterUser):
    """ Создает нового пользователя в БД """
    salt = get_random_string()
    hashed_password = hash_password(user.password, salt)

    new_user = User(email=user.email, username=user.username, hashed_password=f"{salt}${hashed_password}")
    session = await get_async_session()
    session.add(new_user)
    await session.commit()


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        # authorization: str = request.headers.get("Authorization")
        authorization: str = request.cookies.get("access_token")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param

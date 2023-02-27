import datetime
import os
from typing import AsyncGenerator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, ForeignKey, DateTime, text, Text

from Learning.task_manager.config import Settings

BASE_DIR = os.path.dirname(os.path.abspath(__name__))  # Определение пути текущего файла


class Base(DeclarativeBase):
    pass


# Определяем модель таблицы базы данных для SQLAlchemy
class User(Base):
    __tablename__ = 'user'  # Именовать лучше в единственном числе
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    registered_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)


class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    title = Column(String, nullable=False)
    is_complete = Column(Boolean, default=False)


class Token(Base):
    __tablename__ = 'token'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    token = Column(Text, nullable=False, default=lambda: str(uuid4()).replace('-', ''), unique=True)
    expires = Column(DateTime, default=False)


engine = create_async_engine(
    Settings(BASE_DIR).db_url,
    connect_args={'check_same_thread': False},
    echo=True
)

"""
    Создадим объект локальной сессии, чтобы каждая операция с задачами была независимой и в отдельной сессии. 
    Таким образом, каждый экземлпяр self.local_session будет сеансом БД
    
    autocommit=False - Сами будем управлять операциями CRUD в БД
    autoflush=False - Отключаем доступ к данным, которые еще не сохранены в БД
    bind=self.engine - Подключаем соединение с нашей базой данных
"""

async_session_maker = async_sessionmaker(
    engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


async def create_db_and_tables() -> None:
    """
        Метод создает все таблицы для Базы Данных SQlite.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncSession:
    """
        Метод создает нам экземпляр сессии и отдает для использования и закрывает сессию по выполнении.
    """
    async with async_session_maker() as session:
        return session

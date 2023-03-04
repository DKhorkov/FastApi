import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, ForeignKey, DateTime, Text
from uuid import uuid4


class TestBase(DeclarativeBase):
    pass


class TestUser(TestBase):
    __tablename__ = 'test_user'  # Именовать лучше в единственном числе
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    registered_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)


class TestTask(TestBase):
    __tablename__ = 'test_task'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("test_user.id"))
    title = Column(String, nullable=False)
    is_complete = Column(Boolean, default=False)


class TestToken(TestBase):
    __tablename__ = 'test_token'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("test_user.id"))
    token = Column(Text, nullable=False, default=lambda: str(uuid4()).replace('-', ''), unique=True)
    expires = Column(DateTime, default=False)


test_db_url = "sqlite+aiosqlite:///test_database.db"

test_engine = create_async_engine(
    test_db_url,
    connect_args={'check_same_thread': False},
    echo=True
)

test_async_session_maker = async_sessionmaker(
    test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_test_async_session() -> AsyncSession:
    """
        Метод создает нам экземпляр сессии и отдает для использования и закрывает сессию по выполнении.
    """
    async with test_async_session_maker() as session:
        return session


async def create_test_db_and_tables() -> None:
    """
        Метод создает все таблицы для Базы Данных SQlite.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)

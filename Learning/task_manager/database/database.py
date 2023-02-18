import os
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy import create_engine

from Learning.task_manager.config import Settings

BASE_DIR = os.path.dirname(os.path.abspath(__name__))  # Определение пути текущего файла

Base = declarative_base()


# Определяем модель таблицы базы данных для SQLAlchemy
class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    is_complete = Column(Boolean, default=False)


class Alchemy:

    def __init__(self):
        """
        echo - информирование об операциях БД в консоль
        check_same_thread - Для запуска БД не только в основном треде
        """
        self.engine = create_engine(Settings(BASE_DIR).db_url,
                                    connect_args={'check_same_thread': False},
                                    echo=True)
        Base.metadata.create_all(bind=self.engine)  # Создаем таблицы

        """
        Создадим объект локальной сессии, чтобы каждая операция с задачами была независимой и в отдельной сессии. Таким
        образом, каждый экземлпяр self.local_session будет сеансом БД
        
        autocommit=False - Сами будем управлять операциями CRUD в БД
        autoflush=False - Отключаем доступ к данным, которые еще не сохранены в БД
        bind=self.engine - Подключаем соединение с нашей базой данных
        """
        self.local_session = sessionmaker(autocommit=False,
                                          autoflush=False,
                                          bind=self.engine)

    def get_session(self):
        """Метод создает нам экземпляр сессии и отдает для использования и закрывает сессию по выполнении"""
        session = self.local_session()
        try:
            return session
        finally:
            session.close()


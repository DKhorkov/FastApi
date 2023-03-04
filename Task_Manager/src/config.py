from pydantic import BaseSettings


class Settings(BaseSettings):

    app_name = "Менеджер задач на FastAPI"
    db_url = "sqlite+aiosqlite:///task_manager.db"  # URL необходим для соединения через SQLAlchemy

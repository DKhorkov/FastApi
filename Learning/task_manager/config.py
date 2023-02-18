from pydantic import BaseSettings


class Settings(BaseSettings):

    app_name = "Менеджер задач на FastAPI"
    db_url = f"sqlite:///task_manager.db"  # URL необходим для соединения через SQLAlchemy

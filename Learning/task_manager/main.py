import uvicorn
import os

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates  # Шаблонизатор

from routers import user_router
from routers import db_router

task_manager = FastAPI()

# Добавляем роутеры, которые были созданы в рамках других пакетов для облегчения основного файла и создания модальности:
task_manager.include_router(db_router)
task_manager.include_router(user_router)

# Привязываем CSS. StaticFiles необходимо для того, чтобы корректно описать, где наша CSS директория:
task_manager.mount(
    path='/static',
    app=StaticFiles(directory='static'),
    name='static'
)

templates = Jinja2Templates(directory='/templates/task_manager')  # Указываем, где будут лежать наши HTML шаблоны


def create_logging_folder() -> None:
    """
        Функция проверяет, существует ли папка для логов и, если нет, создает ее.

        :return: None
    """
    if not os.path.exists('log'):
        os.mkdir('log')


if __name__ == '__main__':
    create_logging_folder()
    uvicorn.run("main:task_manager", host="0.0.0.0", port=os.getenv("PORT", default=8080), log_level="info")

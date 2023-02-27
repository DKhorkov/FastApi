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
    app=StaticFiles(directory='./static/task_manager'),
    name='static'
)

templates = Jinja2Templates(directory='./templates/task_manager')  # Указываем, где будут лежать наши HTML шаблоны

if __name__ == '__main__':
    uvicorn.run("main:task_manager", host="0.0.0.0", port=os.getenv("PORT", default=8080), log_level="info")

import uvicorn
import os

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates  # Шаблонизатор
from starlette.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER, HTTP_302_FOUND
from sqlalchemy.orm import Session

from database.database import Alchemy, Task
from config import Settings

db = Alchemy()
task_manager = FastAPI()


@task_manager.get("/", name='home', response_class=HTMLResponse)
async def home_page(request: Request, session: Session = Depends(db.get_session)):
    """
        Функция получает все созданные заявки и возвращает отрисованный HTML шаблон с данными заявками.

        :param request: обязательный параметр запроса для нашей странички по аналогии с Django
        :param session: объект сессии из SQLAlchemy. В нее передаются зависимости нашей базы данных.
        :return: отрисованный HTML, созданный с помощью шаблонизатора Jinja2Templates
    """
    all_tasks = session.query(Task).all()
    return templates.TemplateResponse(
        name="home.html",  # Путь до шаблона
        context={'request': request,  # Context - данные, которые мы передаем в шаблон
                 'app_name': Settings().app_name,
                 'tasks_list': all_tasks},
        status_code=200,
    )


@task_manager.post("/add", name='add', response_class=RedirectResponse)
async def home_page(title: str = Form(..., description="Укажите описание заявки"),
                    session: Session = Depends(db.get_session)):
    """
        Функция получает название новой заявки, создает экземлпяр модели заявки и созраняет заявку в базу данных.
        Переадресовывает на домашнюю страницу.

        :param title: обязательный параметр формы, для создания новой заявки
        :param session: объект сессии из SQLAlchemy. В нее передаются зависимости нашей базы данных.
        :return: отрисованный HTML, созданный с помощью шаблонизатора Jinja2Templates
    """
    new_task = Task(title=title)
    session.add(new_task)
    session.commit()

    home_url = task_manager.url_path_for('home')
    return RedirectResponse(url=home_url, status_code=HTTP_303_SEE_OTHER)


@task_manager.get('/update/{task_id}', name='update', response_class=RedirectResponse)
async def update(task_id: int, session: Session = Depends(db.get_session)):
    """
        Функция получает идентификационный номер заявки, находит ее и меняет статус на противпомоложный от того,
        который был.

        :param task_id: идентификационный номер заявки для редактирования
        :param session: объект сессии из SQLAlchemy. В нее передаются зависимости нашей базы данных.
        :return: отрисованный HTML, созданный с помощью шаблонизатора Jinja2Templates
    """
    task_to_update = session.query(Task).filter(Task.id == task_id).first()
    task_to_update.is_complete = not task_to_update.is_complete
    session.commit()

    url = task_manager.url_path_for('home')

    return RedirectResponse(url=url, status_code=HTTP_302_FOUND)


@task_manager.get('/delete/{task_id}', name='delete', response_class=RedirectResponse)
async def delete(task_id: int, session: Session = Depends(db.get_session)):
    """
        Функция получает идентификационный номер заявки, находит ее и удаляет.

        :param task_id: идентификационный номер заявки для редактирования
        :param session: объект сессии из SQLAlchemy. В нее передаются зависимости нашей базы данных.
        :return: отрисованный HTML, созданный с помощью шаблонизатора Jinja2Templates
    """
    task_to_delete = session.query(Task).filter_by(id=task_id).first()
    session.delete(task_to_delete)
    session.commit()

    url = task_manager.url_path_for('home')
    return RedirectResponse(url=url, status_code=HTTP_302_FOUND)


# StaticFiles необходимо для того, чтобы корректно описать, где наша CSS директория
task_manager.mount(path='/static',
                   app=StaticFiles(directory='./static/task_manager'),
                   name='static')
templates = Jinja2Templates(directory='./templates/task_manager')  # Указываем, где будут лежать наши HTML шаблоны

if __name__ == '__main__':
    uvicorn.run("main:task_manager", host="0.0.0.0", port=os.getenv("PORT", default=8080), log_level="info")

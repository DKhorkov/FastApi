import uvicorn
import os

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates  # Шаблонизатор
from starlette.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER, HTTP_302_FOUND
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from database.database import Task, User, create_db_and_tables, get_async_session
from users.models import RegisterUser
from users.utils import get_user_by_email, create_user, get_user_by_token, validate_password, \
    create_user_token, OAuth2PasswordBearerWithCookie
from config import Settings

task_manager = FastAPI()
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="auth")


async def get_current_user(token: str = Depends(oauth2_scheme)):
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


@task_manager.post("/auth", name='auth',
                   response_class=RedirectResponse,
                   # response_model=TokenBase
                   )
async def auth(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_email(email=form_data.username)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not validate_password(
            password=form_data.password, hashed_password=user.hashed_password
    ):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = await create_user_token(user_id=user.id)

    login_url = task_manager.url_path_for('tasks')
    response = RedirectResponse(url=login_url, status_code=HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {token.token}", httponly=True)
    # return token

    return response


@task_manager.on_event("startup")
async def on_startup():
    """Создаем все таблицы на старте"""
    await create_db_and_tables()


@task_manager.get('/', name='start', response_class=HTMLResponse)
def start_page(request: Request):
    return templates.TemplateResponse(
        name="start_page.html",  # Путь до шаблона
        context={'request': request,  # Context - данные, которые мы передаем в шаблон
                 'app_name': Settings().app_name,
                 },
        status_code=200,
    )


@task_manager.get('/login', name='login', response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse(
        name="login.html",
        context={'request': request,
                 'app_name': Settings().app_name,
                 },
        status_code=200,
    )


@task_manager.get('/register', name='register', response_class=HTMLResponse)
def register(request: Request):
    return templates.TemplateResponse(
        name="register.html",
        context={'request': request,
                 'app_name': Settings().app_name,
                 },
        status_code=200,
    )


@task_manager.post("/process_register")
async def process_register(email=Form(...), username=Form(...), password=Form(...)):
    db_user = await get_user_by_email(email=email)
    if db_user:
        raise HTTPException(status_code=400, detail='User already exists')
    user = RegisterUser(email=email, password=password, username=username)
    await create_user(user=user)

    login_url = task_manager.url_path_for('login')
    return RedirectResponse(url=login_url, status_code=HTTP_303_SEE_OTHER)


@task_manager.get("/tasks", name='tasks', response_class=HTMLResponse)
async def tasks(request: Request, session: Session = Depends(get_async_session),
                current_user: User = Depends(get_current_user)):
    """
        Функция получает все созданные заявки и возвращает отрисованный HTML шаблон с данными заявками.
        :param request: обязательный параметр запроса для нашей странички по аналогии с Django
        :param current_user: текущий пользователь, под которого будут выведены созданные им заявки
        :param session: объект сессии из SQLAlchemy. В нее передаются зависимости нашей базы данных.
        :return: отрисованный HTML, созданный с помощью шаблонизатора Jinja2Templates
    """
    async with session as async_session:
        all_tasks = await async_session.execute(select(Task).filter(Task.user_id == current_user.id))
        all_tasks = all_tasks.scalars()  # Переводим в скалярный вид для доступа к таскам и отрисовки в шаблонах HTML

    return templates.TemplateResponse(
        name="tasks.html",  # Путь до шаблона
        context={'request': request,  # Context - данные, которые мы передаем в шаблон
                 'app_name': Settings().app_name,
                 'tasks_list': all_tasks},
        status_code=200,
    )


@task_manager.post("/add", name='add', response_class=RedirectResponse)
async def add(title: str = Form(..., description="Укажите описание заявки"),
              session: Session = Depends(get_async_session),
              current_user: User = Depends(get_current_user)):
    """
        Функция получает название новой заявки, создает экземлпяр модели заявки и созраняет заявку в базу данных.
        Переадресовывает на домашнюю страницу.
        :param title: обязательный параметр формы, для создания новой заявки
        :param session: объект сессии из SQLAlchemy. В нее передаются зависимости нашей базы данных.
        :param current_user: текущий пользователь, под которого будут выведены созданные им заявки
        :return: отрисованный HTML, созданный с помощью шаблонизатора Jinja2Templates
    """
    new_task = Task(title=title, user_id=current_user.id)
    async with session as async_session:
        async_session.add(new_task)
        await async_session.commit()

    home_url = task_manager.url_path_for('tasks')
    return RedirectResponse(url=home_url, status_code=HTTP_303_SEE_OTHER)


@task_manager.get('/update/{task_id}', name='update', response_class=RedirectResponse)
async def update(task_id: int, session: Session = Depends(get_async_session),
                 current_user: User = Depends(get_current_user)):
    """
        Функция получает идентификационный номер заявки, находит ее и меняет статус на противпомоложный от того,
        который был.
        :param task_id: идентификационный номер заявки для редактирования
        :param session: объект сессии из SQLAlchemy. В нее передаются зависимости нашей базы данных.
        :param current_user: текущий пользователь, под которого будут выведены созданные им заявки
        :return: отрисованный HTML, созданный с помощью шаблонизатора Jinja2Templates
    """
    async with session as async_session:
        task_to_update = await async_session.execute(select(Task).filter(Task.id == task_id))
        task_to_update = task_to_update.scalar()

        # Проверка, что таска принадлежит текущему пользователю:
        if not task_to_update.user_id == current_user.id:
            raise HTTPException(status_code=404, detail='Fuck u asshole!')

        task_to_update.is_complete = not task_to_update.is_complete
        await async_session.commit()

    url = task_manager.url_path_for('tasks')

    return RedirectResponse(url=url, status_code=HTTP_302_FOUND)


@task_manager.get('/delete/{task_id}', name='delete', response_class=RedirectResponse)
async def delete(task_id: int, session: Session = Depends(get_async_session),
                 current_user: User = Depends(get_current_user)):
    """
        Функция получает идентификационный номер заявки, находит ее и удаляет.
        :param task_id: идентификационный номер заявки для редактирования
        :param session: объект сессии из SQLAlchemy. В нее передаются зависимости нашей базы данных.
        :param current_user: текущий пользователь, под которого будут выведены созданные им заявки
        :return: отрисованный HTML, созданный с помощью шаблонизатора Jinja2Templates
    """
    async with session as async_session:
        task_to_delete = await async_session.execute(select(Task).filter_by(id=task_id))
        task_to_delete = task_to_delete.scalar()

        # Проверка, что таска принадлежит текущему пользователю:
        if not task_to_delete.user_id == current_user.id:
            raise HTTPException(status_code=404, detail='Fuck u asshole!')

        await async_session.delete(task_to_delete)
        await async_session.commit()

    url = task_manager.url_path_for('tasks')
    return RedirectResponse(url=url, status_code=HTTP_302_FOUND)


# StaticFiles необходимо для того, чтобы корректно описать, где наша CSS директория
task_manager.mount(path='/static',
                   app=StaticFiles(directory='./static/task_manager'),
                   name='static')
templates = Jinja2Templates(directory='./templates/task_manager')  # Указываем, где будут лежать наши HTML шаблоны

if __name__ == '__main__':
    uvicorn.run("main:task_manager", host="0.0.0.0", port=os.getenv("PORT", default=8080), log_level="info")

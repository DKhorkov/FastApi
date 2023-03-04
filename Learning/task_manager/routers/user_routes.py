import logging

from fastapi import Request, Form, HTTPException, APIRouter
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from starlette.templating import Jinja2Templates
from typing import Optional

from Learning.task_manager.config import Settings
from Learning.task_manager.users.utils import get_user_by_email, create_user, validate_password, \
    create_user_token
from Learning.task_manager.users.models import RegisterUser


logging.basicConfig(format='[%(asctime)s: %(levelname)s] %(message)s', filename='./log/user_logs', filemode='a')
logger = logging.getLogger("")
logger.setLevel(level=logging.DEBUG)

user_router = APIRouter()
templates = Jinja2Templates(directory='./templates/task_manager')  # Указываем, где будут лежать наши HTML шаблоны


@user_router.post("/auth", name='auth', response_class=Optional[RedirectResponse | HTMLResponse])
async def auth(request: Request, email: str = Form(default=None), password: str = Form(default=None)):
    """
        Функция получает email и пароль пользователя и проверяет, зарегистрирован ли пользователь с таким email-ом.
        Если пользователь зарегистрирован, идет проверка валидности введенного пароля.
        Если пароль валидный, то создается токен для данного юзера, сохраняется в БД и добавляется в cookies ответа
        RedirectResponse, который перенаправляет пользователя на страницу с его задачами.

        :param request: Базовый запрос
        :param email: Email пользователя
        :param password: Пароль пользователя

        :return: RedirectResponse на страницу с задачами текущего пользователя
    """
    try:
        if not email or not password:
            return templates.TemplateResponse(
                name="login.html",
                context={'request': request,
                         'app_name': Settings().app_name,
                         'incorrect_creds': False,
                         'empty_creds': True
                         },
                status_code=200,
            )

        user = await get_user_by_email(email=email)
        if not user:
            return templates.TemplateResponse(
                name="login.html",
                context={'request': request,
                         'app_name': Settings().app_name,
                         'incorrect_creds': True,
                         'empty_creds': False
                         },
                status_code=200,
            )

        if not validate_password(password=password, hashed_password=user.hashed_password):
            return templates.TemplateResponse(
                name="login.html",
                context={'request': request,
                         'app_name': Settings().app_name,
                         'incorrect_creds': True,
                         'empty_creds': False
                         },
                status_code=200,
            )

        token = await create_user_token(user_id=user.id)

        login_url = '/tasks'
        response = RedirectResponse(url=login_url, status_code=HTTP_303_SEE_OTHER)
        response.set_cookie(key="access_token", value=f"Bearer {token.token}", httponly=True)
        return response

    except Exception as e:
        logger.debug(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@user_router.get('/', name='start', response_class=HTMLResponse)
def start_page(request: Request):
    """
        :param request: Стандартный запрос

        :return: Отрисованный HTML шаблон со стартовой страницей для авторизации или регистрации
    """
    try:
        return templates.TemplateResponse(
            name="start_page.html",  # Путь до шаблона
            context={'request': request,  # Context - данные, которые мы передаем в шаблон
                     'app_name': Settings().app_name,
                     },
            status_code=200,
        )

    except Exception as e:
        logger.debug(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@user_router.get('/logout', name='logout', response_class=RedirectResponse)
def logout():
    """
        Функция стирает cookies и переадресовывает юзера на стартовую страницу.

        :return: RedirectResponse на стартовую страницу
    """
    try:
        redirect_url = user_router.url_path_for('start')
        response = RedirectResponse(url=redirect_url, status_code=HTTP_303_SEE_OTHER)
        response.delete_cookie(key="access_token", httponly=True)
        return response

    except Exception as e:
        logger.debug(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@user_router.get('/login', name='login', response_class=HTMLResponse)
def login(request: Request):
    """
        :param request: Стандартный запрос

        :return: Отрисованный HTML шаблон с формой для авторизации
    """
    try:
        return templates.TemplateResponse(
            name="login.html",
            context={'request': request,
                     'app_name': Settings().app_name,
                     'incorrect_creds': False,
                     'empty_creds': False
                     },
            status_code=200,
        )

    except Exception as e:
        logger.debug(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@user_router.get('/register', name='register', response_class=HTMLResponse)
def register(request: Request):
    """
        :param request: Стандартный запрос

        :return: Отрисованный HTML шаблон с формой для регистрации
    """
    try:
        return templates.TemplateResponse(
            name="register.html",
            context={'request': request,
                     'app_name': Settings().app_name,
                     'user_exists': False,
                     'empty_creds': False
                     },
            status_code=200,
        )

    except Exception as e:
        logger.debug(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@user_router.post("/process_register", response_class=Optional[RedirectResponse | HTMLResponse])
async def process_register(request: Request, email=Form(default=None), username=Form(default=None),
                           password=Form(default=None)):
    """
        Функция обрабатывает входящие данные из HTML формы и создает пользователя в БД, если пользователя с таким же
        адресом электронной почты еще не зарегистрировано, после чего перенаправляет пользователя на страницу
        авторизации.

        :param request: Базовый запрос
        :param email: Адрес электронной почты из HTML формы
        :param username: Имя пользователя из HTML формы
        :param password: Пароль из HTML формы

        :return: RedirectResponse на страницу для авторизации (login)
    """
    try:
        if not email or not password or not username:
            return templates.TemplateResponse(
                name="register.html",
                context={'request': request,
                         'app_name': Settings().app_name,
                         'user_exists': False,
                         'empty_creds': True
                         },
                status_code=200,
            )

        db_user = await get_user_by_email(email=email)
        if db_user:
            logger.debug(f'User tried to register with email={email}, but user with those email is already exists!')
            return templates.TemplateResponse(
                name="register.html",
                context={'request': request,
                         'app_name': Settings().app_name,
                         'user_exists': True,
                         'empty_creds': False
                         },
                status_code=200,
            )

        user = RegisterUser(email=email, password=password, username=username)
        await create_user(user=user)

        login_url = user_router.url_path_for('login')
        return RedirectResponse(url=login_url, status_code=HTTP_303_SEE_OTHER)

    except Exception as e:
        logger.debug(e)
        raise HTTPException(status_code=500, detail="Something went wrong")

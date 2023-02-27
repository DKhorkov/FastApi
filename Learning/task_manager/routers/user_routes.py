from fastapi import Request, Form, Depends, HTTPException, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from starlette.templating import Jinja2Templates

from Learning.task_manager.config import Settings
from Learning.task_manager.users.utils import get_user_by_email, create_user, validate_password, \
    create_user_token
from Learning.task_manager.users.models import RegisterUser


user_router = APIRouter()
templates = Jinja2Templates(directory='./templates/task_manager')  # Указываем, где будут лежать наши HTML шаблоны


@user_router.post("/auth", name='auth', response_class=RedirectResponse)
async def auth(form_data: OAuth2PasswordRequestForm = Depends()):
    """
        Функция получает email и пароль пользователя и проверяет, зарегистрирован ли пользователь с таким email-ом.
        Если пользователь зарегистрирован, идет проверка валидности введенного пароля.
        Если пароль валидный, то создается токен для данного юзера, сохраняется в БД и добавляется в cookies ответа
        RedirectResponse, который перенаправляет пользователя на страницу с его задачами.

        :param form_data:  Email и password из HTML формы, валидирующиеся через OAuth2

        :return: RedirectResponse на страницу с задачами текущего пользователя
    """
    user = await get_user_by_email(email=form_data.username)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not validate_password(
            password=form_data.password, hashed_password=user.hashed_password
    ):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = await create_user_token(user_id=user.id)

    login_url = '/tasks'
    response = RedirectResponse(url=login_url, status_code=HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {token.token}", httponly=True)
    return response


@user_router.get('/', name='start', response_class=HTMLResponse)
def start_page(request: Request):
    """
        :param request: Стандартный запрос

        :return: Отрисованный HTML шаблон со стартовой страницей для авторизации или регистрации
    """
    return templates.TemplateResponse(
        name="start_page.html",  # Путь до шаблона
        context={'request': request,  # Context - данные, которые мы передаем в шаблон
                 'app_name': Settings().app_name,
                 },
        status_code=200,
    )


@user_router.get('/login', name='login', response_class=HTMLResponse)
def login(request: Request):
    """
        :param request: Стандартный запрос

        :return: Отрисованный HTML шаблон с формой для авторизации
    """
    return templates.TemplateResponse(
        name="login.html",
        context={'request': request,
                 'app_name': Settings().app_name,
                 },
        status_code=200,
    )


@user_router.get('/register', name='register', response_class=HTMLResponse)
def register(request: Request):
    """
        :param request: Стандартный запрос

        :return: Отрисованный HTML шаблон с формой для регистрации
    """
    return templates.TemplateResponse(
        name="register.html",
        context={'request': request,
                 'app_name': Settings().app_name,
                 },
        status_code=200,
    )


@user_router.post("/process_register", response_class=RedirectResponse)
async def process_register(email=Form(...), username=Form(...), password=Form(...)):
    """
        Функция обрабатывает входящие данные из HTML формы и создает пользователя в БД, если пользователя с таким же
        адресом электронной почты еще не зарегистрировано, после чего перенаправляет пользователя на страницу авторизации.

        :param email: Адрес электронной почты из HTML формы
        :param username: Имя пользователя из HTML формы
        :param password: Пароль из HTML формы

        :return: RedirectResponse на страницу для авторизации (login)
    """
    db_user = await get_user_by_email(email=email)
    if db_user:
        raise HTTPException(status_code=400, detail='User already exists')
    user = RegisterUser(email=email, password=password, username=username)
    await create_user(user=user)

    login_url = user_router.url_path_for('login')
    return RedirectResponse(url=login_url, status_code=HTTP_303_SEE_OTHER)

from httpx import AsyncClient
from sqlalchemy.future import select

from .session_for_test import get_test_async_session, TestToken, TestTask


async def test_create_task(get_test_async_client: AsyncClient):

    # Регистрируем и "логиним" пользователя:
    await get_test_async_client.post(
        "/test_process_register",
        data={
            'email': 'test_email@mail.ru',
            'username': 'test_user',
            'password': 'test_password'
        }
    )

    await get_test_async_client.post(
        "/test_auth",
        data={
            'username': 'test_email@mail.ru',
            'password': 'test_password'
        }
    )

    session = await get_test_async_session()
    test_token = await session.execute(select(TestToken).filter(TestToken.user_id == 1))
    test_token = test_token.scalar()

    # Убеждаемся, что пока что нет ни одной задачи:
    test_tasks = await session.execute(select(TestTask))
    assert len(test_tasks.scalars().all()) == 0

    response = await get_test_async_client.post(
        "/test_add",
        data={'title': 'test_task'},
        cookies={"access_token": f"Bearer {test_token.token}"},
    )

    assert response.status_code == 303

    test_tasks = await session.execute(select(TestTask))
    assert len(test_tasks.scalars().all()) == 1


async def test_update_task(get_test_async_client: AsyncClient):

    session = await get_test_async_session()

    # Проверяем, что до обновления статус - не завершен:
    test_task = await session.execute(select(TestTask).filter(TestTask.user_id == 1))
    test_task = test_task.scalar()
    assert test_task.is_complete is False

    response = await get_test_async_client.get(
        "/test_update/1"
    )

    assert response.status_code == 302

    # Убеждаемся, что статус задачи изменился:
    await session.refresh(test_task)
    assert test_task.is_complete is True


async def test_tasks_view(get_test_async_client: AsyncClient):

    response = await get_test_async_client.get(
        "/test_tasks"
    )
    assert response.status_code == 200


async def test_update_task_not_related_to_user(get_test_async_client: AsyncClient):

    # Регистрируем и "логиним" другого пользователя:
    await get_test_async_client.post(
        "/test_process_register",
        data={
            'email': 'test_email_to_fake@mail.ru',
            'username': 'test_user',
            'password': 'test_password'
        }
    )

    await get_test_async_client.post(
        "/test_auth",
        data={
            'username': 'test_email_to_fake@mail.ru',
            'password': 'test_password'
        }
    )

    session = await get_test_async_session()

    # Убеждаемся, что сейчас есть задача, но она не принадлежит текущему пользователю, а также, что она завершена:
    all_test_tasks = await session.execute(select(TestTask))
    current_user_test_tasks = await session.execute(select(TestTask).filter(TestTask.user_id == 2))
    assert len(all_test_tasks.scalars().all()) == 1
    assert len(current_user_test_tasks.scalars().all()) == 0
    test_task = await session.execute(select(TestTask).filter(TestTask.user_id == 1))
    test_task = test_task.scalar()
    assert test_task.is_complete is True

    test_token = await session.execute(select(TestToken).filter(TestToken.user_id == 2))
    test_token = test_token.scalar()

    await get_test_async_client.get(
        "/test_update/1",
        cookies={"access_token": f"Bearer {test_token.token}"},
    )

    # Убеждаемся, что статус задачи не изменился:
    await session.refresh(test_task)
    assert test_task.is_complete is True


async def test_delete_task_not_related_to_user(get_test_async_client: AsyncClient):

    session = await get_test_async_session()

    # Убеждаемся, что сейчас есть задача, но она не принадлежит текущему пользователю:
    all_test_tasks = await session.execute(select(TestTask))
    current_user_test_tasks = await session.execute(select(TestTask).filter(TestTask.user_id == 2))
    assert len(all_test_tasks.scalars().all()) == 1
    assert len(current_user_test_tasks.scalars().all()) == 0

    await get_test_async_client.get(
        "/test_delete/1"
    )

    # Убеждаемся, что задача не была удалена:
    test_tasks_after_trying_to_delete = await session.execute(select(TestTask))
    assert len(test_tasks_after_trying_to_delete.scalars().all()) == 1


async def test_delete_task(get_test_async_client: AsyncClient):

    # Авторизуемся за владельца задачи для ее дальнейшего удаления:
    await get_test_async_client.post(
        "/test_auth",
        data={
            'username': 'test_email@mail.ru',
            'password': 'test_password'
        }
    )

    session = await get_test_async_session()
    test_token = await session.execute(select(TestToken).filter(TestToken.user_id == 1))
    test_token = test_token.scalar()

    # Проверяем, что до удаления есть существующая задача:
    test_task = await session.execute(select(TestTask))
    assert len(test_task.scalars().all()) == 1

    response = await get_test_async_client.get(
        "/test_delete/1",
        cookies={"access_token": f"Bearer {test_token.token}"},
    )

    assert response.status_code == 302

    # Убеждаемся, что задачa удалена:
    test_task = await session.execute(select(TestTask))
    assert len(test_task.scalars().all()) == 0

if __name__ == '__main__':
    test_create_task(AsyncClient)
    test_update_task(AsyncClient)
    test_tasks_view(AsyncClient)
    test_update_task_not_related_to_user(AsyncClient)
    test_delete_task_not_related_to_user(AsyncClient)
    test_delete_task(AsyncClient)

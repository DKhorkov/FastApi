import os
import uvicorn
from fastapi import FastAPI, Query, Body, Request, status

"""https://www.youtube.com/watch?v=AXYgXpHJhBA&list=PLaED5GKTiQG8GW5Rv2hf3tRS-d9t9liUt&index=3"""

app = FastAPI()

@app.get('/')
async def hello_world():
    return {"Hello": "World"}


@app.post('/post_number/{number_id}')
async def post_number(number_id: int, q: str = 'Query is empty'):
    """Передаем по URL номер, являющийся числом, а также запрос-стрингу. FastApi самостоятельно проводит валидацию
    данных"""
    return {'number_id': number_id, 'query': q}


"""Чтобы отправить тело запроса на сервер, например, необходимо создать схему модели

Для вывода класса модели в теле ответа необходимо использовать приравнение параметра метода к Body(..., embed=True)"""
from Task_Manager.base_api.base_api_models import Animal


@app.post('/post_animal')
async def post_animal(animal: Animal = Body(..., embed=True)):
    return {'name': animal.name, 'species': animal.species, 'age': animal.age, 'birthday': animal.birthday,
            'relatives': animal.relatives}


"""Валидация Query, например минимальной длины запроса или максимальной

Чтобы сделать параметр обязательным, нужно указать default=...

Также можно создать множественный Query как в примере метода get_multiple_numbers()

Если параметр устаревший и в скором времени может быть удален - можно указать для уведомления об этом deprecated=True"""
from Task_Manager.base_api.base_api_exceptions import InvalidTypeException


@app.get('/get_number')
async def get_number(q: str = Query(default=..., min_length=5, max_length=20,
                                    description="Write some number to get it's echo")):
    if not q.isnumeric():
        return {'Error': InvalidTypeException(int).message}
    return {'Query': q}


from typing import List


@app.get('/get_multiple_numbers')
async def get_multiple_numbers(q: List[int] = Query(default=..., description="Write numbers to get there echo")):
    return {'Query': q}


"""Также можно сделать GET метод, в основе которого будет ENUM class. 
Так пользователь сможет выбирать из атрибутов ENUM """
from Task_Manager.base_api.base_api_models import EnumAnimals


@app.get('/get_enum_animals')
async def get_enum_animals(enum_animals: EnumAnimals):
    features: dict = {'Rat': 'Rat has 4 legs and a tail!',
                      'Chicken': 'Chicken has 2 legs and feathers!',
                      'Crocodile': 'Crocodile has 4 legs and tail, and very huge and dangerous teeth!'}
    return {'Animal': enum_animals, 'Feature': features[enum_animals.value]}


"""Чтобы масштабировать тело ответа, можно использовать несколько моделей.

Также помимо валидации входных данных на их тип можно писать собственную валидацию (см. модель Master)"""
from Task_Manager.base_api.base_api_models import Master


@app.post('/post_multiple_body')
def post_multiple_body(animal: Animal = Body(..., embed=True), master: Master = Body(..., embed=True)):
    return {'animal': animal, 'master': master}


"""Работа с телом ответа и response_model:

Для примеры была создана модель Friends с заданными по умолчанию значениями.

Для отображения данных, которые отдаст сервер необходимо указать в методе response_model.

response_model_exclude_unset=True - уберет из тела ответа все параметры, которые были указаны по умолчанию в модели,
даже если им были переданы значения в request.

response_model_exclude={'ages'} - работает по аналогии с response_model_exclude_unset, но удаляет только указанные.

response_model_include является противоположность response_model_exclude и вернет ТОЛЬКО указанные данные.
"""
from Task_Manager.base_api.base_api_models import Friends


@app.post('/friends', response_model=Friends, response_model_exclude={'ages'})
def post_friends(friends: Friends = Body(..., embed=True, description='Friends and their ages')):
    return {'friends': friends}


"""
Можно принимать одну модель на вход и возвращать другую на выход. Например, на вход мы принимаем BookIn, а на выходе
возвращаем BookOut, который уже имеет id книги в книжном магазине

Но, в данном случае, мы не можем просто вернуть {'book': book}, поскольку у данной модели нет атрибута id_in_shop.
Для этого применим метод перевода модели в словарь и добавим ей значение атрибута id_in_shop

return BookOut(**book_in.dict(), id_in_shop=3) - аналог того, что ниже, но короче и удобнее (синтаксический сахар):
                        book = book_in.dict()
                        book['id_in_shop'] = 3
                        return book
"""
from Task_Manager.base_api.base_api_models import BookIn, BookOut


@app.post('/book', response_model=BookOut)
def post_book(book_in: BookIn):
    return BookOut(**book_in.dict(), id_in_shop=3)


"""В случае, если мы хотим возвращать юзеру вместо сообщения с текстом "Internal server error" трассировку, 
которую видим на сервере, то можно сделать обработчик нужного нам Exception и отправить его."""
from fastapi.exceptions import ValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exception: ValidationError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        content=jsonable_encoder({'error logs': exception}))


if __name__ == '__main__':
    uvicorn.run("base_api:app", host="0.0.0.0", port=os.getenv("PORT", default=8090), log_level="info")

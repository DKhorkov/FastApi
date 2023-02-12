from fastapi import FastAPI, Query

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


"""Чтобы отправить тело запроса на сервер, например, необходимо создать схему модели"""
from .base_api_models import Animal


@app.post('/post_animal')
async def post_animal(animal: Animal):
    return {'name': animal.name, 'species': animal.species, 'age': animal.age, 'birthday': animal.birthday,
            'relatives': animal.relatives}


"""Валидация Query, например минимальной длины запроса или максимальной

Чтобы сделать параметр обязательным, нужно указать default=...

Также можно создать множественный Query как в примере метода get_multiple_numbers()

Если параметр устаревший и в скором времени может быть удален - можно указать для уведомления об этом deprecated=True"""
from .base_api_exceptions import InvalidTypeException


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
from .base_api_models import EnumAnimals


@app.get('/get_enum_animals')
async def get_enum_animals(enum_animals: EnumAnimals):
    features: dict = {'Rat': 'Rat has 4 legs and a tail!',
                      'Chicken': 'Chicken has 2 legs and feathers!',
                      'Crocodile': 'Crocodile has 4 legs and tail, and very huge and dangerous teeth!'}
    return {'Animal': enum_animals, 'Feature': features[enum_animals.value]}

from pydantic import BaseModel, validator, Field
from datetime import date
from typing import List, Dict, Optional
from enum import Enum


class Relatives(BaseModel):
    name: str


class Animal(BaseModel):
    species: str = None  # Необязательный атрибут
    name: str
    age: int
    birthday: date

    """Допустим, мы хотим передавать список, для этого нужно создать модель под список на основе pydantic"""
    relatives: List[Relatives]


class EnumAnimals(str, Enum):
    rat: str = 'Rat'
    chicken: str = 'Chicken'
    crocodile: str = 'Crocodile'


class Master(BaseModel):
    """Один из способов валидации - декоратор @validator и написание валидирующей функции после него.
    Второй способ - Field. Ставим многоточие, чтобы сделать поле обязательным."""

    name: str = 'Dmitriy'
    surname: Optional[str] = ""  # Делаем поле опциональным, а дефолтное значение пустым
    age: int = 0
    pets: int = Field(...,
                      ge=0,  # Greater than or equal to
                      lt=10,  # Less than
                      description='Number of pets should be in range from 0 to 9 inclusively'
                      )

    @validator('age')
    def check_age(cls, value_from_request):  # именно cls, а не self
        if value_from_request < 0:
            raise ValueError
        return value_from_request


class Friends(BaseModel):

    names: List[str] = []
    ages: List[int] = []
    names_and_ages: Dict[str, int] = {}


class BookIn(BaseModel):

    title: str
    author: str
    copies_sold: int


class BookOut(BookIn):

    id_in_shop: int

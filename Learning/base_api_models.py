from pydantic import BaseModel
from datetime import date
from typing import List
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

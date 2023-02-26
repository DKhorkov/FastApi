from typing import Optional
from pydantic import UUID4, BaseModel, EmailStr, Field, validator
from datetime import datetime


class RegisterUser(BaseModel):
    """ Проверяет запрос на регистрацию"""
    email: EmailStr
    username: str
    password: str


class TokenBase(BaseModel):
    """
        Field(..., alias=«access_token») устанавливает псевдоним access_token для поля token.
        Для обозначения, что поле обязательно, в качестве первого параметра передается специальное значение "..."
    """
    token: UUID4 = Field(..., alias="access_token")
    expires: datetime
    token_type: Optional[str] = "bearer"

    class Config:
        allow_population_by_field_name = True

    @validator("token")
    def hexlify_token(cls, value):
        """ Конвертирует UUID в hex строку """
        return value.hex

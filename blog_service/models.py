from pydantic import BaseModel, Field, BeforeValidator
from typing import Annotated, List, Optional
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]


class UserRegister(BaseModel):
    """
    Схема для входящих данных регистрации и базовой аутентификации.
    """
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    """
    Схема ответа при возврате данных пользователя.
    """
    id: PyObjectId = Field(validation_alias="_id")
    username: str
    created_at: datetime


class CommentCreate(BaseModel):
    """Схема входящих данных для создания комментария к посту."""
    username: str
    password: str
    text: str = Field(..., min_length=1, max_length=500)


class CommentUpdate(BaseModel):
    """Схема входящих данных для редактирования существующего комментария."""
    username: str
    password: str
    text: str = Field(..., min_length=1, max_length=500)


class CommentResponse(BaseModel):
    """Схема для возврата информации о комментарии"""
    id: str
    author_username: str
    text: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class PostCreate(BaseModel):
    """Схема входящих данных для создания нового поста"""
    username: str
    password: str
    title: str = Field(..., min_length=3, max_length=120)
    content: str = Field(..., min_length=5)
    tags: List[str] = Field(default_factory=list)


class PostResponse(BaseModel):
    """Схема ответа для отображения поста"""
    id: PyObjectId = Field(validation_alias="_id")
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    author_username: str
    author_id: str
    created_at: datetime
    comments: List[CommentResponse] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class PostUpdate(BaseModel):
    """Схема входящих данных для редактирования поста."""
    username: str
    password: str
    title: str
    content: str
    tags: Optional[List[str]] = []


class PostDelete(BaseModel):
    """Схема для подтверждения прав автора при удалении поста или комментария"""
    username: str
    password: str

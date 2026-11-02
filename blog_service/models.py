from pydantic import BaseModel, Field, BeforeValidator
from typing import Annotated, List, Optional
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: PyObjectId = Field(validation_alias="_id")
    username: str
    created_at: datetime


class CommentCreate(BaseModel):
    username: str
    password: str
    text: str = Field(..., min_length=1, max_length=500)


class CommentUpdate(BaseModel):
    username: str
    password: str
    text: str = Field(..., min_length=1, max_length=500)


class CommentResponse(BaseModel):
    id: str
    author_username: str
    text: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class PostCreate(BaseModel):
    username: str
    password: str
    title: str = Field(..., min_length=3, max_length=120)
    content: str = Field(..., min_length=5)
    tags: List[str] = Field(default_factory=list)


class PostResponse(BaseModel):
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
    username: str
    password: str
    title: str
    content: str
    tags: Optional[List[str]] = []


class PostDelete(BaseModel):
    username: str
    password: str

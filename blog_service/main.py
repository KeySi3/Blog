from fastapi import FastAPI, Depends, status, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import lifespan, get_db
from models import UserRegister, UserResponse, PostCreate, PostResponse, CommentCreate, CommentResponse, CommentUpdate, \
    PostUpdate, PostDelete
from motor.motor_asyncio import AsyncIOMotorDatabase
from auth_utils import hash_password, verify_password
from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from bson.errors import InvalidId
import uuid

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

@app.get(
    "/register",
    response_class=HTMLResponse,
    summary="Страница регистрации"
)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


@app.get("/login", response_class=HTMLResponse, summary="Страница авторизации")
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/", response_class=HTMLResponse, summary="Главная страница")
async def index_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/posts/view/{post_id}", response_class=HTMLResponse, summary="Страница поста с комментариями")
async def post_detail_page(request: Request, post_id: str):
    return templates.TemplateResponse(request=request, name="post_detail.html", context={"post_id": post_id})


@app.get("/profile", response_class=HTMLResponse, summary="Личная страница автора")
async def profile_page(request: Request):
    return templates.TemplateResponse(request=request, name="profile.html")

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя"
)
async def register(
    user_data: UserRegister,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    existing_user = await db["users"].find_one({
        "username": user_data.username
    })

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким логином уже существует"
        )

    user_doc = {
        "username": user_data.username,
        "password_hash": hash_password(user_data.password),
        "created_at": datetime.now(timezone.utc)
    }

    result = await db["users"].insert_one(user_doc)
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    return created_user


@app.post("/auth/login", response_model=UserResponse, summary="Проверка логина и пароля")
async def login(
    credentials: UserRegister,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await db["users"].find_one({"username": credentials.username})

    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )

    return user


@app.get("/api/posts", response_model=List[PostResponse], summary="Получение списка постов для отображения на главной странице")
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=50),
    q: Optional[str] = None,
    tag: Optional[str] = None,
    author: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    filter_query = {}
    # Поиск по заголовку
    if q:
        filter_query["title"] = {"$regex": q, "$options": "i"}

    # Фильтр по тегу
    if tag:
        filter_query["tags"] = tag.strip().lower()

    # Фильтр по автору поста
    if author:
        filter_query["author_username"] = author.strip()

    cursor = db["posts"].find(filter_query).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


@app.get("/api/posts/{post_id}", response_model=PostResponse, summary="Получение одного поста")
async def get_single_post(post_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        oid = ObjectId(post_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Некорректный ID")

    post = await db["posts"].find_one({"_id": oid})
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return post


@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED, summary="Создание поста")
async def create_post(post_data: PostCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db["users"].find_one({"username": post_data.username})
    if not user or not verify_password(post_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    cleaned_tags = [t.strip().lower() for t in post_data.tags if t.strip()]

    post_doc = {
        "title": post_data.title,
        "content": post_data.content,
        "tags": cleaned_tags,
        "author_username": user["username"],
        "author_id": str(user["_id"]),
        "created_at": datetime.now(timezone.utc),
        "comments": [],
        "updated_at": None
    }
    result = await db["posts"].insert_one(post_doc)
    return await db["posts"].find_one({"_id": result.inserted_id})


@app.post("/api/posts/{post_id}/comments", response_model=CommentResponse, summary="Добавление комментария")
async def add_comment(
    post_id: str,
    comment_data: CommentCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        oid = ObjectId(post_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Некорректный ID")

    user = await db["users"].find_one({"username": comment_data.username})
    if not user or not verify_password(comment_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверные учетные данные для комментария")

    comment_obj = {
        "id": str(uuid.uuid4()),
        "author_username": user["username"],
        "text": comment_data.text,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }

    res = await db["posts"].update_one(
        {"_id": oid},
        {"$push": {"comments": comment_obj}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Пост не найден")

    return comment_obj


@app.put(
    "/api/posts/{post_id}/comments/{comment_id}",
    response_model=CommentResponse,
    summary="Редактирование комментария автором"
)
async def update_comment(
    post_id: str,
    comment_id: str,
    comment_data: CommentUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        oid = ObjectId(post_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Некорректный ID поста")

    user = await db["users"].find_one({"username": comment_data.username})
    if not user or not verify_password(comment_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    now = datetime.now(timezone.utc)

    update_result = await db["posts"].update_one(
        {
            "_id": oid,
            "comments": {
                "$elemMatch": {
                    "id": comment_id,
                    "author_username": user["username"]
                }
            }
        },
        {
            "$set": {
                "comments.$.text": comment_data.text,
                "comments.$.updated_at": now
            }
        }
    )

    if update_result.matched_count == 0:
        existing_post = await db["posts"].find_one({"_id": oid, "comments.id": comment_id})
        if not existing_post:
            raise HTTPException(status_code=404, detail="Комментарий или пост не найден")
        raise HTTPException(status_code=403, detail="Вы можете редактировать только свои комментарии")

    updated_post = await db["posts"].find_one(
        {"_id": oid},
        {"comments": {"$elemMatch": {"id": comment_id}}}
    )
    return updated_post["comments"][0]


@app.put(
    "/api/posts/{post_id}",
    response_model=PostResponse,
    summary="Редактирование поста автором"
)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        oid = ObjectId(post_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Некорректный ID поста")

    user = await db["users"].find_one({"username": post_data.username})
    if not user or not verify_password(post_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    post = await db["posts"].find_one({"_id": oid})
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    if post["author_username"] != user["username"]:
        raise HTTPException(status_code=403, detail="Вы можете редактировать только свои посты")

    cleaned_tags = [t.strip().lower() for t in post_data.tags if t.strip()]

    await db["posts"].update_one(
        {"_id": oid},
        {
            "$set": {
                "title": post_data.title,
                "content": post_data.content,
                "tags": cleaned_tags,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return await db["posts"].find_one({"_id": oid})


@app.delete(
    "/api/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление поста автором"
)
async def delete_post(
    post_id: str,
    delete_data: PostDelete,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        oid = ObjectId(post_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Некорректный ID поста")

    user = await db["users"].find_one({"username": delete_data.username})
    if not user or not verify_password(delete_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    post = await db["posts"].find_one({"_id": oid})
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    if post["author_username"] != user["username"]:
        raise HTTPException(status_code=403, detail="Вы можете удалять только свои посты")

    await db["posts"].delete_one({"_id": oid})
    return None


@app.delete(
    "/api/posts/{post_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление комментария автором"
)
async def delete_comment(
    post_id: str,
    comment_id: str,
    delete_data: PostDelete,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        oid = ObjectId(post_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Некорректный ID поста")

    user = await db["users"].find_one({"username": delete_data.username})
    if not user or not verify_password(delete_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    post = await db["posts"].find_one(
        {
            "_id": oid,
            "comments.id": comment_id
        },
        {"comments.$": 1}
    )

    if not post or not post["comments"]:
        raise HTTPException(status_code=404, detail="Комментарий или пост не найден")

    comment = post["comments"][0]
    if comment["author_username"] != user["username"]:
        raise HTTPException(status_code=403, detail="Вы можете удалять только свои комментарии")

    await db["posts"].update_one(
        {"_id": oid},
        {"$pull": {"comments": {"id": comment_id}}}
    )

    return None


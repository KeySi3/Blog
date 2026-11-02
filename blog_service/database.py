from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(settings.mongodb_url)
    try:
        await app.state.mongo_client.admin.command("ping")
        print(" Успешное подключение к MongoDB")
    except Exception as e:
        print(f" Ошибка подключения к MongoDB: {e}")
        raise e
    yield
    app.state.mongo_client.close()


async def get_db(request: Request) -> AsyncIOMotorDatabase:
    client: AsyncIOMotorClient = request.app.state.mongo_client
    return client[settings.database_name]
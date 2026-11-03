from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения:
    - Код до yield выполняется перед стартом сервера (startup).
    - Код после yield выполняется при корректном завершении работы сервера (shutdown).
    """
    app.state.mongo_client = AsyncIOMotorClient(settings.mongodb_url)
    try:
        await app.state.mongo_client.admin.command("ping")
        print(" Успешное подключение к MongoDB")
    except Exception as e:
        print(f" Ошибка подключения к MongoDB: {e}")
        raise e
    # Точка передачи управления приложению
    yield
    # Закрыть клиент и все активные соединения пула при остановке сервера
    app.state.mongo_client.close()


async def get_db(request: Request) -> AsyncIOMotorDatabase:
    client: AsyncIOMotorClient = request.app.state.mongo_client
    return client[settings.database_name]

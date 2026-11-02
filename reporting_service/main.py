from fastapi import FastAPI, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import lifespan, get_db

app = FastAPI(title="Reporting & Analytics Service", lifespan=lifespan)

@app.get("/reports/summary", summary="Общая сводка по блогу")
async def get_summary(db: AsyncIOMotorDatabase = Depends(get_db)):
    total_posts = await db["posts"].count_documents({})
    total_users = await db["users"].count_documents({})
    return {
        "total_posts": total_posts,
        "total_users": total_users
    }

@app.get("/reports/authors-stats", summary="Статистика активности авторов")
async def get_authors_stats(db: AsyncIOMotorDatabase = Depends(get_db)):
    # MongoDB Aggregation Pipeline для подсчета количества публикаций по каждому автору
    pipeline = [
        {"$group": {"_id": "$author_username", "posts_count": {"$sum": 1}}},
        {"$sort": {"posts_count": -1}},
        {"$project": {"author": "$_id", "posts_count": 1, "_id": 0}}
    ]
    cursor = db["posts"].aggregate(pipeline)
    return await cursor.to_list(length=100)
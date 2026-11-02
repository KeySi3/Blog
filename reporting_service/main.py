from fastapi import FastAPI, HTTPException, status
from models import StatsResponse
from config import BLOG_SERVICE_URL
import httpx
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Reporting Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://blog_service:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/stats", response_model=StatsResponse, summary="Получить статистику по постам и комментариям")
async def get_stats():
    total_posts = 0
    total_comments = 0
    skip = 0
    batch_size = 50

    async with httpx.AsyncClient(base_url=BLOG_SERVICE_URL, timeout=10.0) as client:
        while True:
            try:
                response = await client.get("/api/posts", params={"skip": skip, "limit": batch_size})
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Ошибка соединения с основным сервисом: {exc}"
                )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Основной сервис вернул ошибку: {response.status_code}"
                )
            posts = response.json()
            if not posts:
                break

            total_posts += len(posts)
            for post in posts:
                comments = post.get("comments")
                total_comments += len(comments)

            if len(posts) < batch_size:
                break

            skip += batch_size
    return StatsResponse(
        total_posts=total_posts,
        total_comments=total_comments
    )

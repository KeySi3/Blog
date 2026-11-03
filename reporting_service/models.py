from pydantic import BaseModel


class StatsResponse(BaseModel):
    """Схема для отправки данных с отчетом"""
    total_posts: int
    total_comments: int

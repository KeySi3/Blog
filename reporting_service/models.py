from pydantic import BaseModel


class StatsResponse(BaseModel):
    total_posts: int
    total_comments: int

from datetime import datetime

from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    homepage_url: str

    class Config:
        from_attributes = True


class ArticleResponse(BaseModel):
    id: int
    title: str
    author: str | None
    url: str
    image_url: str | None
    summary: str
    content_snippet: str | None
    dedupe_key: str
    popularity_score: int
    published_at: datetime
    category: CategoryResponse
    source: SourceResponse
    is_bookmarked: bool = False

    class Config:
        from_attributes = True


class FeedResponse(BaseModel):
    items: list[ArticleResponse]
    total: int


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    preferences: list[CategoryResponse]

    class Config:
        from_attributes = True


class UpdatePreferencesRequest(BaseModel):
    category_ids: list[int]


class BookmarkRequest(BaseModel):
    user_id: int
    article_id: int


class MessageResponse(BaseModel):
    message: str

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class NewsSourceCreate(BaseModel):
    source: str = Field(..., max_length=255)
    baseurl: HttpUrl
    kafka_topic: str
    category: str
    country: str
    language: str
    status: bool = True
    priority: int = 1


class NewsSourceUpdate(BaseModel):
    source: str | None = None
    baseurl: HttpUrl | None = None
    kafka_topic: str | None = None
    category: str | None = None
    country: str | None = None
    language: str | None = None
    status: bool | None = None
    priority: int | None = None


class NewsSourceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    baseurl: str
    kafka_topic: str
    category: str
    country: str | None = None
    language: str | None = None
    status: bool
    priority: int
    created_at: datetime
    updated_at: datetime


class NewsSourceResponse(BaseModel):
    items: list[NewsSourceItem]
    total: int
    page: int
    size: int
    pages: int

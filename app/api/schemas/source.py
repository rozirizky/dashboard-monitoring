from datetime import datetime
from typing import Optional

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
    source: Optional[str] = None
    baseurl: Optional[HttpUrl] = None
    kafka_topic: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    status: Optional[bool] = None
    priority: Optional[int] = None


class NewsSourceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    baseurl: str
    kafka_topic: str
    category: str
    country: Optional[str] = None
    language: Optional[str] = None
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

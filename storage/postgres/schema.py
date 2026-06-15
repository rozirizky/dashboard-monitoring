
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)






class SourceBase(BaseModel):
    name: str = Field(..., max_length=255)
    domain: str = Field(..., max_length=255)
    country: Optional[str] = Field(None, max_length=10)
    default_language: Optional[str] = Field(None, max_length=10)


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=10)
    default_language: Optional[str] = Field(None, max_length=10)


class SourceResponse(_OrmBase, SourceBase):
    id: uuid.UUID
    created_at: datetime






class ArticleTagResponse(_OrmBase):
    id: uuid.UUID
    article_id: uuid.UUID
    tag: str
    created_at: datetime






class NlpResultBase(BaseModel):
    category: Optional[str] = Field(None, max_length=100)
    sentiment_label: Optional[str] = Field(None, max_length=50)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    score_positive: Optional[float] = Field(None, ge=0.0, le=1.0)
    score_negative: Optional[float] = Field(None, ge=0.0, le=1.0)
    score_neutral: Optional[float] = Field(None, ge=0.0, le=1.0)
    analyzed_at: Optional[datetime] = None


class NlpResultResponse(_OrmBase, NlpResultBase):
    id: uuid.UUID
    article_id: uuid.UUID
    created_at: datetime






class StorageRefBase(BaseModel):
    bucket: Optional[str] = Field(None, max_length=255)
    object_name: Optional[str] = None
    storage_tier: str = Field("raw-news", max_length=50)
    stored_at: Optional[datetime] = None


class StorageRefResponse(_OrmBase, StorageRefBase):
    id: uuid.UUID
    article_id: uuid.UUID
    created_at: datetime






class ArticleBase(BaseModel):
    url_hash: str = Field(..., max_length=64)
    content_hash: Optional[str] = Field(None, max_length=64)

    source_id: Optional[uuid.UUID] = None
    source_name: Optional[str] = Field(None, max_length=255)
    source_domain: Optional[str] = Field(None, max_length=255)

    title: Optional[str] = Field(None, max_length=1024)
    author: Optional[str] = Field(None, max_length=512)
    url: Optional[str] = None
    content_clean: Optional[str] = None
    summary: Optional[str] = None          

    language: Optional[str] = Field(None, max_length=10)
    category: Optional[str] = Field(None, max_length=100)
    topic: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=10)

    published_date: Optional[date] = None
    crawled_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class ArticleCreate(ArticleBase):
    tags: list[str] = Field(default_factory=list)
    nlp_result: Optional[NlpResultBase] = None
    storage_ref: Optional[StorageRefBase] = None

    @field_validator("tags", mode="before")
    @classmethod
    def split_semicolon_tags(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split(";") if t.strip()]
        return v


class ArticleUpdate(BaseModel):
    content_hash: Optional[str] = Field(None, max_length=64)
    title: Optional[str] = Field(None, max_length=1024)
    author: Optional[str] = Field(None, max_length=512)
    content_clean: Optional[str] = None
    summary: Optional[str] = None
    language: Optional[str] = Field(None, max_length=10)
    category: Optional[str] = Field(None, max_length=100)
    topic: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=10)
    published_date: Optional[date] = None
    crawled_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class ArticleResponse(_OrmBase, ArticleBase):
    id: uuid.UUID
    created_at: datetime
    tags: list[ArticleTagResponse] = []
    nlp_result: Optional[NlpResultResponse] = None
    storage_ref: Optional[StorageRefResponse] = None


class ArticleListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ArticleResponse]
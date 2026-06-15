from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalysisSchema(BaseModel):
    sentiment: str | None = None
    confidence: float | None = None
    summary: str | None = None


class ArticleSourceSchema(BaseModel):
    id: int
    name: str


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None = None
    url: str | None = None
    category: str | None = None
    country: str | None = None
    published_date: datetime | None = None
    source: ArticleSourceSchema
    analysis: AnalysisSchema
    tags: list[str] = []

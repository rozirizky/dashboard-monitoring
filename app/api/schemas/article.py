from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AnalysisSchema(BaseModel):
    sentiment: Optional[str] = None
    confidence: Optional[float] = None
    summary: Optional[str] = None


class ArticleSourceSchema(BaseModel):
    id: int
    name: str


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    published_date: Optional[datetime] = None
    source: ArticleSourceSchema
    analysis: AnalysisSchema
    tags: list[str] = []

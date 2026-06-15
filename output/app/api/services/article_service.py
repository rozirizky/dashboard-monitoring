from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.models.analysis import Analysis
from app.api.models.article import Article
from app.api.models.article_storage import ArticleStorageRef
from app.api.models.article_tags import ArticleTag


class ArticleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def insert(
        self,
        article_data: dict,
        nlp_data: dict,
        storage_data: dict,
    ) -> Article:
        existing = await self.db.execute(
            select(Article).where(Article.url_hash == article_data["url_hash"])
        )
        article = existing.scalar_one_or_none()
        if article:
            return article

        article = Article(**article_data)
        article.nlp_result = Analysis(
            sentiment_label=nlp_data.get("sentiment_label"),
            confidence_score=nlp_data.get("confidence_score"),
            summary=nlp_data.get("summary"),
        )
        article.storage_ref = ArticleStorageRef(
            bucket=storage_data["bucket"],
            object_name=storage_data["object_name"],
        )
        article.tags = [ArticleTag(tag=tag) for tag in nlp_data.get("tags", [])]

        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def get_articles(self, limit: int = 100, offset: int = 0) -> list[dict]:
        result = await self.db.execute(
            select(Article)
            .options(
                selectinload(Article.source),
                selectinload(Article.nlp_result),
                selectinload(Article.tags),
            )
            .order_by(Article.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        articles = result.scalars().all()
        return [
            {
                "id": a.id,
                "title": a.title,
                "url": a.url,
                "category": a.category,
                "country": a.country,
                "published_date": a.published_date,
                "source": {"id": a.source.id, "name": a.source.source},
                "analysis": {
                    "sentiment": a.nlp_result.sentiment_label if a.nlp_result else None,
                    "confidence": a.nlp_result.confidence_score if a.nlp_result else None,
                    "summary": a.nlp_result.summary if a.nlp_result else None,
                },
                "tags": [tag.tag for tag in a.tags],
            }
            for a in articles
        ]

    async def get_article(self, article_id: int) -> Article | None:
        result = await self.db.execute(
            select(Article)
            .options(
                selectinload(Article.source),
                selectinload(Article.nlp_result),
                selectinload(Article.tags),
                selectinload(Article.storage_ref),
            )
            .where(Article.id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_by_category(self, category: str) -> list[Article]:
        result = await self.db.execute(
            select(Article)
            .options(
                selectinload(Article.source),
                selectinload(Article.nlp_result),
                selectinload(Article.tags),
            )
            .where(Article.category == category)
            .order_by(Article.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_sentiment(self, sentiment: str) -> list[Article]:
        result = await self.db.execute(
            select(Article)
            .join(Analysis, Analysis.article_id == Article.id)
            .options(
                selectinload(Article.source),
                selectinload(Article.nlp_result),
                selectinload(Article.tags),
            )
            .where(Analysis.sentiment_label == sentiment)
        )
        return result.scalars().all()

    async def top_news(self, limit: int = 10, offset: int = 0) -> list[Article]:
        result = await self.db.execute(
            select(Article)
            .options(
                selectinload(Article.source),
                selectinload(Article.nlp_result),
                selectinload(Article.tags),
            )
            .order_by(Article.published_date.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

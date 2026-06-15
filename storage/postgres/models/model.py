import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from storage.postgres.models.base import Base , BaseModel


class Source(BaseModel):
    __tablename__ = "sources"

    __table_args__ = (
        UniqueConstraint("domain", name="uq__sources_domain"),
        UniqueConstraint("name", name="uq__sources_name"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String(10))
    default_language: Mapped[Optional[str]] = mapped_column(String(10))

    articles: Mapped[list["Article"]] = relationship(
        "Article",
        back_populates="source",
        lazy="selectin",
    )

class Article(BaseModel):

    __tablename__ = "articles"

    __table_args__ = (
        UniqueConstraint("url_hash", name="uq__articles_url_hash"),
        Index("ix__articles_published_date", "published_date"),
        Index("ix__articles_source_domain", "source_domain"),
        Index("ix__articles_category_language", "category", "language"),
    )

    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))

    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
    )


    # ── Dedup keys ───────────────────────────────────────────────────────
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


    source_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Content ──────────────────────────────────────────────────────────
    title: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_clean: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Classification ───────────────────────────────────────────────────
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # ── Summary ──────────────────────────────────────────────────────────
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────────
    published_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped[Optional["Source"]] = relationship(
        "Source",
        back_populates="articles",
    )
    tags: Mapped[list["ArticleTag"]] = relationship(
        "ArticleTag",
        back_populates="article",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    nlp_result: Mapped[Optional["NlpResult"]] = relationship(
        "NlpResult",
        back_populates="article",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    storage_ref: Mapped[Optional["StorageRef"]] = relationship(
        "StorageRef",
        back_populates="article",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Article url_hash={self.url_hash!r} title={self.title!r}>"


class ArticleTag(BaseModel):
    __tablename__ = "article_tags"

    __table_args__ = (
        Index("ix__article_tags_tag", "tag"),
        UniqueConstraint(
            "article_id",
            "tag",
            name="uq__article_tags_article_tag",
        ),
    )

    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )

    tag: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="tags",
    )

class NlpResult(BaseModel):

    __tablename__ = "nlp_results"

    __table_args__ = (
        UniqueConstraint(
            "article_id",
            name="uq__nlp_results_article_id",
        ),
    )


    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score_positive: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score_negative: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score_neutral: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    article: Mapped["Article"] = relationship(
        "Article", back_populates="nlp_result"
    )

    def __repr__(self) -> str:
        return (
            f"<NlpResult article_id={self.article_id} "
            f"label={self.sentiment_label!r} conf={self.confidence_score}>"
        )


class StorageRef(BaseModel):

    __tablename__ = "storage_refs"
    __table_args__ = (
        UniqueConstraint("article_id", name="uq__storage_refs_article_id"),
    )

    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    bucket: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    object_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="raw-news"
    )
    stored_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    article: Mapped["Article"] = relationship(
        "Article", back_populates="storage_ref"
    )

    def __repr__(self) -> str:
        return (
            f"<StorageRef article_id={self.article_id} "
            f"bucket={self.bucket!r} object={self.object_name!r}>"
        )
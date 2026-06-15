from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.api.db.session import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    source_id: Mapped[int] = mapped_column(
        ForeignKey("news_sources.id"),
        nullable=False,
        index=True,
    )

    url_hash: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(1000),
        nullable=True,
    )

    author: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )

    topic: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )

    country: Mapped[str] = mapped_column(
        String(10),
        nullable=True,
    )

    published_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    source = relationship(
        "NewsSource",
        back_populates="articles",
    )

    nlp_result = relationship(
        "Analysis",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )

    storage_ref = relationship(
        "ArticleStorageRef",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )

    tags = relationship(
        "ArticleTag",
        back_populates="article",
        cascade="all, delete-orphan",
    )
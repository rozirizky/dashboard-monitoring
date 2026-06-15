from sqlalchemy import Boolean, Integer, String , DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.db.session import Base

from datetime import datetime
class NewsSource(Base):
    __tablename__ = "news_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    baseurl: Mapped[str] = mapped_column(String(2000), nullable=False)
    kafka_topic: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


    articles = relationship(
        "Article",
        back_populates="source",
        lazy="selectin",
    )

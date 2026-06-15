from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.db.session import Base


class ArticleStorageRef(Base):
    __tablename__ = "article_storage_refs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), unique=True, nullable=False)
    bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    object_name: Mapped[str] = mapped_column(String(2000), nullable=False)

    article = relationship("Article", back_populates="storage_ref")

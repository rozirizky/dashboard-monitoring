from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.db.session import get_db
from app.api.services.article_service import ArticleService

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get("")
async def get_articles(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    data = await ArticleService(db).get_articles(limit=limit, offset=offset)
    return {"success": True, "count": len(data), "data": data}


@router.get("/{article_id}")
async def get_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
):
    article = await ArticleService(db).get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"success": True, "data": article}


@router.get("/category/{category}")
async def get_by_category(
    category: str,
    db: AsyncSession = Depends(get_db),
):
    data = await ArticleService(db).get_by_category(category)
    return {"success": True, "count": len(data), "data": data}


@router.get("/sentiment/{sentiment}")
async def get_by_sentiment(
    sentiment: str,
    db: AsyncSession = Depends(get_db),
):
    data = await ArticleService(db).get_by_sentiment(sentiment)
    return {"success": True, "count": len(data), "data": data}

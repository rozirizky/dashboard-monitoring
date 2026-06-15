from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.db.session import get_db
from app.api.schemas.response import ResponseSchema
from app.api.schemas.source import (
    NewsSourceCreate,
    NewsSourceItem,
    NewsSourceResponse,
    NewsSourceUpdate,
)
from app.api.services.source_service import NewsSourceService

router = APIRouter(
    prefix="/news-sources",
    tags=["News Sources"],
)


@router.get("", response_model=ResponseSchema[NewsSourceResponse])
async def list_news_sources(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """Ambil semua news sources dengan pagination & filter."""
    sources, total = await NewsSourceService.get_all(
        db=db,
        page=page,
        size=size,
        search=search,
        category=category,
        enabled=enabled,
    )
    pages = NewsSourceService.calculate_pages(total, size)

    return ResponseSchema(
        message="Berhasil mengambil data news sources",
        data=NewsSourceResponse(
            items=sources,
            total=total,
            page=page,
            size=size,
            pages=pages,
        ),
    )


@router.get("/{source_id}", response_model=ResponseSchema[NewsSourceItem])
async def get_news_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Ambil news source berdasarkan ID."""
    source = await NewsSourceService.get_by_id(db, source_id)

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News source dengan ID {source_id} tidak ditemukan",
        )

    return ResponseSchema(
        message="Berhasil mengambil data news source",
        data=source,
    )


@router.post(
    "",
    response_model=ResponseSchema[NewsSourceItem],
    status_code=status.HTTP_201_CREATED,
)
async def create_news_source(
    payload: NewsSourceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Buat news source baru."""
    source = await NewsSourceService.create(db, payload)

    return ResponseSchema(
        message="News source berhasil dibuat",
        data=source,
    )


@router.put("/{source_id}", response_model=ResponseSchema[NewsSourceItem])
async def update_news_source(
    source_id: int,
    payload: NewsSourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update news source berdasarkan ID."""
    existing = await NewsSourceService.get_by_id(db, source_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News source dengan ID {source_id} tidak ditemukan",
        )

    source = await NewsSourceService.update(db, source_id, payload)

    return ResponseSchema(
        message="News source berhasil diupdate",
        data=source,
    )


@router.delete("/{source_id}", response_model=ResponseSchema)
async def delete_news_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Hapus news source berdasarkan ID."""
    deleted = await NewsSourceService.delete(db, source_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News source dengan ID {source_id} tidak ditemukan",
        )

    return ResponseSchema(message="News source berhasil dihapus")

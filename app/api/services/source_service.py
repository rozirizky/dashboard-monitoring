import math
from typing import Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models.source_model import NewsSource
from app.api.schemas.source import NewsSourceCreate, NewsSourceUpdate


class NewsSourceService:

    @staticmethod
    async def get_all(
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        category: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> tuple[list[NewsSource], int]:
        query = select(NewsSource)
        count_query = select(func.count()).select_from(NewsSource)

        if search:
            filter_expr = NewsSource.source.ilike(f"%{search}%")
            query = query.where(filter_expr)
            count_query = count_query.where(filter_expr)

        if category:
            filter_expr = NewsSource.category == category
            query = query.where(filter_expr)
            count_query = count_query.where(filter_expr)

        if enabled is not None:
            filter_expr = NewsSource.status == enabled
            query = query.where(filter_expr)
            count_query = count_query.where(filter_expr)

        total = await db.scalar(count_query)
        offset = (page - 1) * size

        result = await db.execute(
            query.order_by(NewsSource.priority.asc())
            .offset(offset)
            .limit(size)
        )

        return list(result.scalars().all()), total or 0

    @staticmethod
    def calculate_pages(total: int, size: int) -> int:
        return math.ceil(total / size) if size > 0 else 0

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        source_id: int,
    ) -> Optional[NewsSource]:
        result = await db.execute(
            select(NewsSource).where(NewsSource.id == source_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_source_by_priority(
        db: AsyncSession,
    ) -> list[NewsSource]:
        result = await db.execute(
            select(NewsSource)
            .where(NewsSource.status.is_(True))
            .order_by(NewsSource.priority.asc())
        )
        return result.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession,
        data: NewsSourceCreate,
    ) -> NewsSource:
        source = NewsSource(**data.model_dump(mode="json"))
        db.add(source)
        
        await db.flush()
        await db.commit()
        await db.refresh(source)
        return source

    @staticmethod
    async def update(
        db: AsyncSession,
        source_id: int,
        data: NewsSourceUpdate,
    ) -> Optional[NewsSource]:
        payload = data.model_dump(exclude_unset=True, exclude_none=True)

        if not payload:
            return await NewsSourceService.get_by_id(db, source_id)

        await db.execute(
            update(NewsSource)
            .where(NewsSource.id == source_id)
            .values(**payload)
        )
        await db.flush()

        return await NewsSourceService.get_by_id(db, source_id)

    @staticmethod
    async def delete(
        db: AsyncSession,
        source_id: int,
    ) -> bool:
        result = await db.execute(
            delete(NewsSource).where(NewsSource.id == source_id)
        )
        return result.rowcount > 0

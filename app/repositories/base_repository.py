import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.models.mixins import BaseMixin

ModelType = TypeVar("ModelType", bound=BaseMixin)


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        query = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(
        self, 
        id: uuid.UUID, 
        obj_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        await self.db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_data)
        )
        await self.db.commit()
        return await self.get_by_id(id)

    async def delete(self, id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def soft_delete(self, id: uuid.UUID) -> Optional[ModelType]:
        obj = await self.get_by_id(id)
        if obj and hasattr(obj, 'soft_delete'):
            obj.soft_delete()
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
        return None

    async def restore(self, id: uuid.UUID) -> Optional[ModelType]:
        obj = await self.get_by_id(id)
        if obj and hasattr(obj, 'restore'):
            obj.restore()
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
        return None

    async def exists(self, id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        query = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(query)
        return len(result.scalars().all())

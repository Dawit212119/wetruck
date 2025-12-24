from abc import ABC
from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

ModelType = TypeVar("ModelType")

class BaseRepository(ABC, Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, db: AsyncSession, organization_id: int):
        self.db = db
        self.organization_id = organization_id
        if not getattr(self, "model", None):
            raise TypeError(f"{self.__class__.__name__} must set model")

    def _is_tenant_aware(self) -> bool:
        return hasattr(self.model, "organization_id")

    def _apply_tenant_scope(self, stmt):
        if self._is_tenant_aware():
            stmt = stmt.where(self.model.organization_id == self.organization_id)
        return stmt

    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        obj_data = obj_in.copy()
        if self._is_tenant_aware():
            obj_data["organization_id"] = self.organization_id
        obj = self.model(**obj_data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get(self, id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        stmt = self._apply_tenant_scope(stmt)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        stmt = select(self.model)
        stmt = self._apply_tenant_scope(stmt)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        obj = await self.get(id)
        if not obj:
            return None
        for key, value in obj_in.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def soft_delete(self, id: int) -> bool:
        stmt = update(self.model).where(
            self.model.id == id
        ).values(deleted=True)
        stmt = self._apply_tenant_scope(stmt)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

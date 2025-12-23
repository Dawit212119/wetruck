from abc import ABC
from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

ModelType = TypeVar("ModelType")


class BaseRepository(ABC, Generic[ModelType]):
    """
    Abstract generic repository for tenant-aware models with soft-delete support.
    
    Concrete repositories must inherit from this class, specifying the model:
    
    class ItemRepository(BaseRepository[Item]):
        pass
    """

    model: type[ModelType]  # Will be set by the generic subclass

    def __init__(self, db: Session, organization_id: int):
        self.db = db
        self.organization_id = organization_id

        # Optional: validate that model is set (helps catch errors early)
        if not getattr(self, "model", None):
            raise TypeError(
                f"{self.__class__.__name__} must specify a model via generic inheritance, "
                "e.g., class MyRepo(BaseRepository[MyModel]): ..."
            )

    def _is_tenant_aware(self) -> bool:
        return hasattr(self.model, "organization_id")

    def _apply_tenant_scope(self, stmt):
        if self._is_tenant_aware():
            stmt = stmt.where(self.model.organization_id == self.organization_id)
        return stmt

    def _apply_deleted_filter(self, stmt, deleted: List[bool]):
        return stmt.where(self.model.deleted.in_(deleted))

    # === CRUD Operations ===

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        obj_data = obj_in.copy()
        if self._is_tenant_aware():
            obj_data["organization_id"] = self.organization_id

        obj = self.model(**obj_data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, id: int, deleted: List[bool] = [False]) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._apply_deleted_filter(stmt, deleted)

        try:
            return self.db.scalars(stmt).one()
        except NoResultFound:
            return None

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        deleted: List[bool] = [False],
    ) -> List[ModelType]:
        stmt = select(self.model)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._apply_deleted_filter(stmt, deleted)
        stmt = stmt.offset(skip).limit(limit).order_by(self.model.id)

        return list(self.db.scalars(stmt).all())

    def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.deleted.is_(False),
        )
        stmt = self._apply_tenant_scope(stmt)

        obj = self.db.scalars(stmt).first()
        if not obj:
            return None

        for key, value in obj_in.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        self.db.commit()
        self.db.refresh(obj)
        return obj

    def soft_delete(self, id: int) -> bool:
        stmt = (
            update(self.model)
            .where(self.model.id == id, self.model.deleted.is_(False))
            .values(deleted=True)
        )
        stmt = self._apply_tenant_scope(stmt)

        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
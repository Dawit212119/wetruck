from abc import ABC
from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from sqlalchemy import Select, String, Integer, Boolean, Date, DateTime, Enum

from src.api.schemas.generic import GenericResponse
from src.core.exception.database_exceptions import DatabaseException, map_sqlalchemy_exception

ModelType = TypeVar("ModelType")


class BaseRepository(ABC, Generic[ModelType]):
    """
    Abstract generic repository for tenant-aware models with soft-delete support.
    
    Concrete repositories must inherit from this class, specifying the model:
    
    class ItemRepository(BaseRepository[Item]):
        pass
    """

    model: type[ModelType]  # Will be set by the generic subclass

    def __init__(self, db: Session, organization_id: Optional[int], tenant_enabled: Optional[bool]=True):
        self.db = db
        self.organization_id = organization_id
        self.tenant_enabled = tenant_enabled

        # Optional: validate that model is set (helps catch errors early)
        if not getattr(self, "model", None):
            raise TypeError(
                f"{self.__class__.__name__} must specify a model via generic inheritance, "
                "e.g., class MyRepo(BaseRepository[MyModel]): ..."
            )

    def _execute(self, fn):
            try:
                return fn()
            except Exception as exc:
                self.db.rollback()
                # 👇 pass the model so unique fields can be resolved dynamically
                raise map_sqlalchemy_exception(exc, model=self.model)

    def _is_tenant_aware(self) -> bool:
        return hasattr(self.model, "organization_id")

    def _apply_tenant_scope(self, stmt):
        if self._is_tenant_aware() and self.tenant_enabled:
            stmt = stmt.where(self.model.organization_id == self.organization_id)
        return stmt

    def _apply_deleted_filter(self, stmt, deleted: List[bool]):
        return stmt.where(self.model.deleted.in_(deleted))

    # === CRUD Operations ===

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        def action():
            data = obj_in.copy()

            if self._is_tenant_aware():
                data["organization_id"] = self.organization_id

            obj = self.model(**data)
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj

        return self._execute(action)
        # try:
        #     obj_data = obj_in.copy()
        #     if self._is_tenant_aware():
        #         obj_data["organization_id"] = self.organization_id

        #     obj = self.model(**obj_data)
        #     self.db.add(obj)
        #     self.db.commit()
        #     self.db.refresh(obj)
        #     return obj
        # except:
        #     raise map_sqlalchemy_exception(exc, model=self.model)

    def get(self, id: int, deleted: List[bool] = [False]) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._apply_deleted_filter(stmt, deleted)

        def action():
            return self.db.scalars(stmt).one()
        return self._execute(action)


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

        # obj = self.db.scalars(stmt).first()
        # if not obj:
        #     return None
        def action():
            obj = self.db.scalars(stmt).one()

            for key, value in obj_in.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            self.db.commit()
            self.db.refresh(obj)
            return obj
        return self._execute(action)

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

    def _apply_filters(self, stmt: Select, filters: Dict[str, Any]) -> Select:
        """
        Generic dynamic filter applicator.
        - Exact match for non-string columns (int, bool, enum, date, etc.)
        - Case-insensitive partial match (ilike) for string columns
        - Ignores None values and unknown attributes
        """
        if filters == None:
            return stmt

        for key, value in filters.items():
            if value is None:
                continue

            if not hasattr(self.model, key):
                continue  # skip unknown fields – safe for optional query params

            column = getattr(self.model, key)

            # Determine the column type
            if isinstance(column.type, String):
                # Partial case-insensitive search for strings
                stmt = stmt.where(column.ilike(f"%{value}%"))
            elif isinstance(column.type, (Integer, Boolean, Date, DateTime, Enum)):
                # Exact match for numbers, booleans, dates, enums
                stmt = stmt.where(column == value)
            else:
                # Fallback: exact match for everything else (e.g., custom types, JSON, etc.)
                stmt = stmt.where(column == value)

        return stmt


    def paginated_list(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Any] = None,
    ) -> GenericResponse[ModelType]:
        filters = filters or {}
        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

        offset = (page - 1) * per_page

        stmt = select(self.model)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._apply_deleted_filter(stmt, [False])
        stmt = self._apply_filters(stmt, filters)

        if order_by:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(self.model.id.desc())

        items = list(self.db.scalars(stmt.offset(offset).limit(per_page)).all())

        count_stmt = select(func.count(self.model.id))
        count_stmt = self._apply_tenant_scope(count_stmt)
        count_stmt = self._apply_deleted_filter(count_stmt, [False])
        count_stmt = self._apply_filters(count_stmt, filters)
        total = self.db.scalar(count_stmt)

        pages = (total + per_page - 1) // per_page if total else 0
        return items, total, page, per_page, pages
    


    def commit(self):
        self.db.commit()

    def refresh(self, instance: object) -> None:
        """
        Refresh the given SQLAlchemy model instance from the database.
        
        This reloads the instance's attributes and relationships from the current
        database state, discarding any in-memory changes that haven't been flushed/committed.
        
        Args:
            instance: The SQLAlchemy model instance to refresh.
        
        Raises:
            sqlalchemy.exc.UnboundExecutionError: If the instance is detached or expired.
        """
        if instance is None:
            raise ValueError("Cannot refresh None instance")
        
        
        self.db.refresh(instance)
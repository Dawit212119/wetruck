# repositories/item.py
from typing import Any, Dict, List, Mapping, Optional, Union

from sqlalchemy import Column, Select, func, select
from src.models.models import User
from src.repositories.base_repository import BaseRepository

FilterType = Union[Dict[str, Any], Dict[Column, Any], Mapping[str | Column, Any]]

class UserRepository(BaseRepository[User]):
    model = User

    def _normalize_filters(self, filters: Optional[FilterType]) -> Dict[str, Any]:
        """
        Convert Column objects to their string attribute names for consistent filtering.
        Handles both Dict[str, Any] and Dict[Column, Any].
        """
        if not filters:
            return {}
        
        normalized = {}
        for key, value in filters.items():
            if isinstance(key, Column):
                # Find the string attribute name from Column (handles aliases too)
                attr_name = None
                for attr_name_cand in dir(self.model):
                    attr = getattr(self.model, attr_name_cand, None)
                    if isinstance(attr, Column) and attr == key:
                        attr_name = attr_name_cand
                        break
                if not attr_name:
                    continue  # Skip unknown columns
                normalized[attr_name] = value
            else:
                # Already a string key
                normalized[str(key)] = value
        return normalized

    def _exists_stmt(
        self,
        filters: Optional[FilterType] = None,
        deleted: List[bool] = [False],
    ) -> Select:
        """
        Build a SELECT statement for existence checks.
        Supports both string attribute names and Column objects.
        """
        stmt = select(func.count(self.model.id) > 0)
        # stmt = self._apply_tenant_scope(stmt)
        stmt = self._apply_deleted_filter(stmt, deleted)
        if filters:
            norm_filters = self._normalize_filters(filters)
            stmt = self._apply_filters(stmt, norm_filters)
        return stmt

    def exists(
        self,
        filters: Optional[FilterType] = None,
        deleted: List[bool] = [False],
    ) -> bool:
        """
        Check if at least one record matches the criteria.
        
        Supports both string attributes and Column objects:
        
        # String attributes (existing usage)
        user_repo.exists(filters={"username": "admin"})
        
        # Model attributes (new!)
        from your_models import User
        user_repo.exists(filters={User.username: "admin"})
        user_repo.exists(filters={User.email: "john@example.com", User.status: "ACTIVE"})
        """
        stmt = self._exists_stmt(filters=filters, deleted=deleted)
        def action():
            return self.db.scalar(stmt)
        return self._execute(action)
    
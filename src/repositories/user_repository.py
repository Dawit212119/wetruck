# repositories/item.py
from typing import Any, Dict, List, Mapping, Optional, Union
from sqlalchemy import Column, Select, func, select
from sqlalchemy.sql.elements import BinaryExpression
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
                    if isinstance(attr, (Column, BinaryExpression)):  # Broader check for safety
                        if attr.is_(key):  # Use identity comparison for columns
                            attr_name = attr_name_cand
                            break
                if attr_name:
                    normalized[attr_name] = value
                # Else: silently skip unknown columns (as before)
            else:
                # Already a string key
                normalized[str(key)] = value
        return normalized

    def _apply_col_filters(self, stmt: Select, filters: Dict[str, Any]) -> Select:
        for attr_name, value in filters.items():
            attr_name = attr_name.replace(self.model.__name__+".", "")
            if hasattr(self.model, attr_name):
                column = getattr(self.model, attr_name)
                stmt = stmt.where(column == value)
            else:
                print(f"Warning: Unknown column {attr_name}")
        return stmt

    def _exists_stmt(
        self,
        filters: Optional[FilterType] = None,
        deleted: List[bool] = [False],
    ) -> Select:
        stmt = select(func.count(self.model.id) > 0)
        # stmt = self._apply_tenant_scope(stmt)
        stmt = self._apply_deleted_filter(stmt, deleted)
        if filters:
            norm_filters = self._normalize_filters(filters)
            stmt = self._apply_col_filters(stmt, norm_filters)
        return stmt

    def exists(
        self,
        filters: Optional[FilterType] = None,
        deleted: List[bool] = [False],
    ) -> bool:
        stmt = self._exists_stmt(filters=filters, deleted=deleted)
        def action():
            return self.db.scalar(stmt)
        return self._execute(action)
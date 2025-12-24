from src.models.models import Truck
from src.repositories.base_repository import BaseRepository


class TruckRepository(BaseRepository[Truck]):
    model = Truck

    # def paginated_list(
    #         self,
    #         page: int = 1,
    #         per_page: int = 20,
    #         filters: Optional[Dict[str, Any]] = None,
    # ) -> Dict[str, Any]:
    #     filters = filters or {}

    #     stmt = select(self.model)
    #     stmt = self._apply_tenant_scope(stmt)
    #     stmt = self._apply_deleted_filter(stmt, [False])
    #     stmt = self._apply_filters(stmt, filters)  # ← uses the smart helper
    #     stmt = stmt.order_by(self.model.id.desc())

    #     offset = (page - 1) * per_page
    #     items = self.db.scalars(stmt.offset(offset).limit(per_page)).all()

    #     count_stmt = select(func.count(self.model.id))
    #     count_stmt = self._apply_tenant_scope(count_stmt)
    #     count_stmt = self._apply_deleted_filter(count_stmt, [False])
    #     count_stmt = self._apply_filters(count_stmt, filters)
    #     total = self.db.scalar(count_stmt)

    #     return {
    #         "items": items,
    #         "total": total,
    #         "page": page,
    #         "per_page": per_page,
    #         "pages": (total + per_page - 1) // per_page,
    #     }

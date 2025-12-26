from fastapi import Depends
from typing import Optional
from sqlalchemy.orm import Session
from src.repositories.dependencies import get_repository
from src.repositories.gps_device_repository import GPSDeviceRepository
from src.core.db.session import get_db
from src.core.security.dependencies import get_current_user
from src.models.models import User


def get_current_organization_id(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Optional[int]:
    """
    Get organization_id from current user.
    Returns None if user doesn't have an organization.
    """
    try:
        user_id = int(user.get("sub"))
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            return db_user.organization_id
    except (TypeError, ValueError):
        pass
    return None


def get_gps_device_repo(organization_id: Optional[int] = None):
    """
    Dependency provider for GPSDeviceRepository.
    Uses existing get_repository() and organization context.
    If organization_id is None, it will be obtained from current user.
    """
    if organization_id is None:
        # Create a dependency that gets org_id from user
        def _get_repo_with_user_org(
            db: Session = Depends(get_db),
            org_id: Optional[int] = Depends(get_current_organization_id),
        ) -> GPSDeviceRepository:
            return GPSDeviceRepository(db=db, organization_id=org_id)
        return _get_repo_with_user_org
    else:
        return get_repository(organization_id=organization_id, repo_cls=GPSDeviceRepository)


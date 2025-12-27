# dependencies.py
from fastapi import Depends,HTTPException,status
from sqlalchemy.orm import Session
from typing import Type, Optional
from src.core.db.session import get_db
from src.core.security.dependencies import get_current_user
from src.models.models import User
from src.repositories.base_repository import BaseRepository
from src.repositories.base_repository import ModelType
# from src.core.context import get_current_organization_id


# NONE TENANT AWARE
def get_repository(
    repo_cls: Type[BaseRepository[ModelType]]
):
    def _get_repo(
        db: Session = Depends(get_db),
    ) -> BaseRepository[ModelType]:
        return repo_cls(db=db, organization_id=None, tenant_enabled=False)    
    return _get_repo


def get_tenant_aware_repository(
    repo_cls: Type[BaseRepository[ModelType]],
):
    """
    Returns a repository instance automatically tenant-aware.
    The organization_id is fetched from the current user token.
    """
    def _get_repo(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ) -> BaseRepository[ModelType]:
        org_id = current_user.get("organization_id")
        if org_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization ID not found in token.",
            )
        return repo_cls(db=db, organization_id=org_id)
    return _get_repo
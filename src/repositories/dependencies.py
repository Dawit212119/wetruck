# dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Type, Optional
from src.core.db.session import get_db
# from src.core.security.dependencies import get_current_user
# from src.models.models import User
from src.repositories.base_repository import BaseRepository
from src.repositories.base_repository import ModelType
# from src.core.context import get_current_organization_id
def get_repository(
    organization_id: Optional[int],
    repo_cls: Type[BaseRepository[ModelType]],
):
    def _get_repo(
        db: Session = Depends(get_db),
        # current_user: User = Depends(get_current_user),
    ) -> BaseRepository[ModelType]:
        return repo_cls(db=db, organization_id=organization_id)
        # return repo_cls(db=db, organization_id=get_current_organization_id())
    
    return _get_repo
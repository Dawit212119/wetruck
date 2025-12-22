# dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Type
from src.core.db.session import get_db
from auth import get_current_user
from src.models import User
from src.repositories import BaseRepository

def get_repository(
    repo_cls: Type[BaseRepository[ModelType]],
):
    def _get_repo(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> BaseRepository[ModelType]:
        return repo_cls(db=db, organization_id=current_user.organization_id)
    
    return _get_repo
# dependencies.py
from fastapi import Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Type
from src.repositories.base_repository import BaseRepository, ModelType
from src.core.db.session import get_db
from src.core.security.dependencies import get_current_user

def get_repository(
    repo_cls: Type[BaseRepository[ModelType]],
):
    async def _get_repo(
        db: AsyncSession = Depends(get_db),
        user: dict = Depends(get_current_user)
    ) -> BaseRepository[ModelType]:

        org_id = user.get("organization_id")  # read safely from token dict
        if not org_id:
            raise HTTPException(401, "organization_id missing in token")

        return repo_cls(db=db, organization_id=org_id)

    return _get_repo

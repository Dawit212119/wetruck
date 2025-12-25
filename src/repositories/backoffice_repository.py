from src.models.models import BackOffice
from src.repositories.base_repository import BaseRepository


class BackOfficeUserRepository(BaseRepository[BackOffice]):
    model = BackOffice


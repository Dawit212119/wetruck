# repositories/item.py
from src.models.models import User
from src.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    model = User
    
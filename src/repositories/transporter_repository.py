from src.models.models import TransporterUser
from src.repositories.base_repository import BaseRepository


class TransporterUserRepository(BaseRepository[TransporterUser]):
    model = TransporterUser

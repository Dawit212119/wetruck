from src.models.models import ShipperUser
from src.repositories.base_repository import BaseRepository


class ShipperUserRepository(BaseRepository[ShipperUser]):
    model = ShipperUser

from src.models.models import Organization
from src.repositories.base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

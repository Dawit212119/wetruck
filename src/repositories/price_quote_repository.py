from src.models.models import PriceQuote
from src.repositories.base_repository import BaseRepository


class PriceQuoteRepository(BaseRepository[PriceQuote]):
    model = PriceQuote

from sqlalchemy import select, or_
from src.repositories.base_repository import BaseRepository
from src.models.models import Document

class DocumentRepository(BaseRepository[Document]):
    model = Document

    # def find_document_by_truck_id():

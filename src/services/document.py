# services/file_service.py

import uuid
from pathlib import Path
from typing import Set

from fastapi import UploadFile, HTTPException, status

from src.api.schemas.document import DocumentResponse
from src.models.models import Document
from src.services.s3_service import S3FileService

ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".jpg", ".jpeg", ".png", ".tiff"}
# Directory to store uploaded files (change to S3 or cloud storage in production)
UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

s3_service = S3FileService()

class DocumentService:
    """Service responsible for handling file uploads and storage."""



    @classmethod
    async def save_on_aws(cls, file: UploadFile, public: bool = False) -> Path:
        return await s3_service.upload_file(file, public=public)
    
    @classmethod
    async def to_document_response(cls, doc: Document) -> DocumentResponse:
        # presigned_url = await DocumentService.generate_presigned_url(doc.file_path)
        presigned_url = await s3_service.generate_presigned_url(doc.file_path)
        
        return DocumentResponse(
            id = doc.id,
            document_type = doc.document_type,
            file_path = doc.file_path,
            truck_id = doc.truck_id,
            driver_id = doc.driver_id,
            created_at = doc.created_at,
            updated_at = doc.updated_at,
            presigned_url = presigned_url
        )

    @classmethod
    async def save_uploaded_file(cls, file: UploadFile) -> Path:
        """
        Validates and saves an uploaded file to the upload directory.
        
        Args:
            file: The uploaded file from FastAPI's UploadFile
            
        Returns:
            Path: The full path to the saved file on disk
            
        Raises:
            HTTPException: 400 if no file or invalid extension
                           500 if saving fails
        """
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file selected"
            )

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File type {file_ext} not allowed. "
                    f"Allowed types: {', '.join(sorted(cls.ALLOWED_EXTENSIONS))}"
                ),
            )

        # Ensure upload directory exists
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Generate unique filename to prevent collisions/overwrites
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        try:
            contents = await file.read()
            file_path.write_bytes(contents)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file"
            ) from exc
        finally:
            await file.close()

        return file_path

    @classmethod
    def get_allowed_extensions(cls) -> Set[str]:
        """Utility to get the list of allowed extensions (e.g., for API docs)."""
        return cls.ALLOWED_EXTENSIONS.copy()
    
    @classmethod
    async def delete_file(cls, object_key: str) -> bool:
        return await s3_service.delete_file(object_key=object_key)
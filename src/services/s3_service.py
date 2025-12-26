# services/file_service.py

import uuid
from pathlib import Path
from typing import Set

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from fastapi import UploadFile, HTTPException, status
from src.core.settings.settings import settings

# from config import (
#     S3_BUCKET_NAME,
#     S3_REGION,
#     S3_UPLOAD_PREFIX,
#     AWS_ACCESS_KEY_ID,
#     AWS_SECRET_ACCESS_KEY,
# )


S3_BUCKET_NAME = settings.s3_bucket_name
S3_REGION = settings.s3_region
S3_UPLOAD_PREFIX = "uploads/"
AWS_ACCESS_KEY_ID = settings.aws_access_key_id
AWS_SECRET_ACCESS_KEY = settings.aws_secret_access_key

class S3FileService:
    """Service for uploading files to Amazon S3."""

    ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".jpg", ".jpeg", ".png", ".tiff"}
    ALLOWED_CONTENT_TYPES: Set[str] = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/tiff",
    }

    def __init__(self):

        session_kwargs = {"region_name": S3_REGION}
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            session_kwargs.update({
                "aws_access_key_id": AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
            })
        
        session = boto3.Session(**session_kwargs)
        self.s3_client = session.client("s3")

    @classmethod
    def _validate_file(cls, file: UploadFile):
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
                    f"Allowed: {', '.join(sorted(cls.ALLOWED_EXTENSIONS))}"
                ),
            )

        # Optional: extra validation using content_type
        if file.content_type not in cls.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content type {file.content_type} not allowed."
            )

    async def upload_file(self, file: UploadFile, public: bool = False) -> str:
        """
        Uploads a file to S3.

        - PDFs will open inline in browser
        - Works with presigned URLs
        - No manual URL signing issues
        """

        self._validate_file(file)

        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        object_key = f"{S3_UPLOAD_PREFIX}{unique_filename}"

        # 🔑 IMPORTANT: These headers MUST be fixed at upload time
        extra_args = {
            "ContentType": file.content_type or "application/octet-stream",
            "ContentDisposition": "inline",
        }

        if public:
            extra_args["ACL"] = "public-read"

        try:
            contents = await file.read()

            self.s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=object_key,
                Body=contents,
                **extra_args,
            )

        except (ClientError, BotoCoreError) as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to S3",
            ) from exc

        finally:
            await file.close()

        # 🚫 DO NOT construct URLs manually for private files
        if public:
            print(f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{object_key}")
            return (
                f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{object_key}"
            )
        print(object_key)
        return object_key
    

    async def upload_file2(self, file: UploadFile, public: bool = False) -> str:
        """
        Uploads a file to S3 and returns the public URL (if public) or the object key.

        Args:
            file: FastAPI UploadFile
            public: If True, makes the file publicly readable (use cautiously!)

        Returns:
            str: Public URL if public=True, otherwise the S3 object key
        """
        self._validate_file(file)

        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        object_key = S3_UPLOAD_PREFIX + unique_filename

        extra_args = {}
        if public:
            extra_args["ACL"] = "public-read"

        try:
            contents = await file.read()
            
            self.s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=object_key,
                Body=contents,
                ContentType=file.content_type or "application/octet-stream",
                **extra_args,
            )
        except (ClientError, BotoCoreError) as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to S3"
            ) from exc
        finally:
            await file.close()

        if public:
            return f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{object_key}"
        else:
            # Return the key (you can generate presigned URLs later when needed)
            return object_key


    async def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        """
        Generates a presigned URL for private files.
        
        Args:
            object_key: The S3 object key returned from upload_file()
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            str: Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET_NAME, 
                        "Key": object_key, 
                        "ResponseContentType": "application/pdf",
                        "ResponseContentDisposition": "inline"},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate presigned URL"
            ) from exc

import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.core.db.session import get_db
from src.domain.enums.document import DocumentTypeEnum
from src.models.models import Document, Driver, Organization, Truck
from src.repositories.dependencies import get_repository, get_tenant_aware_repository
from src.repositories.document_repository import DocumentRepository
from src.repositories.driver_repository import DriverRepository
from src.repositories.organization_repository import OrganizationRepository
from src.repositories.truck_repository import TruckRepository

router = APIRouter()

# Directory to store uploaded files (change to S3 or cloud storage in production)
UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

get_document_repo = get_tenant_aware_repository(DocumentRepository)
get_truck_repo = get_tenant_aware_repository(TruckRepository)
get_organization_repo = get_repository(organization_id=None, repo_cls=OrganizationRepository)
get_driver_repo = get_tenant_aware_repository(DriverRepository)



@router.post(
    "/documents/upload",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    status_code=status.HTTP_201_CREATED,
    summary="Upload a single document attached to truck, driver, or organization",
)
async def upload_single_document(
    document_type: DocumentTypeEnum = Form(..., description="Type of the document"),
    truck_id: Optional[int] = Form(None, description="ID of the truck (if this document belongs to a truck)"),
    driver_id: Optional[int] = Form(None, description="ID of the driver (if this document belongs to a driver)"),
    direct_organization_id: Optional[int] = Form(
        None, description="ID of the organization (if directly attached to organization)"
    ),
    file: UploadFile = File(..., description="The document file to upload"),
    repo: DocumentRepository = Depends(get_document_repo),
    repo_truck: TruckRepository = Depends(get_truck_repo),
    repo_driver: DriverRepository =  Depends(get_driver_repo),
    repo_organization: OrganizationRepository = Depends(get_organization_repo)
    # db: Session = Depends(get_db),
):
    """
    Upload a single document. Exactly one of truck_id, driver_id, or direct_organization_id must be provided.
    The document will be saved to disk and linked to the specified owner.
    """
    # Validate exactly one owner is provided
    provided_owners = [id for id in (truck_id, driver_id, direct_organization_id) if id is not None]
    if len(provided_owners) != 1:
        raise HTTPException(
            status_code=400,
            detail="Exactly one of 'truck_id', 'driver_id', or 'direct_organization_id' must be provided.",
        )

    # Determine owner type and verify existence
    if truck_id:
        owner = repo_truck.get(id = truck_id)
        if not owner:
            raise HTTPException(status_code=404, detail="Truck not found")
    elif driver_id:
        owner = repo_driver.get(id = driver_id)
        if not owner:
            raise HTTPException(status_code=404, detail="Driver not found")
    else:  # direct_organization_id
        owner = repo_organization.get(id = direct_organization_id)
        if not owner:
            raise HTTPException(status_code=404, detail="Organization not found")

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    # Optional: restrict file types or size
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".tiff"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed: {', '.join(allowed_extensions)}",
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file
    try:
        contents = await file.read()
        file_path.write_bytes(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save file")
    finally:
        await file.close()

    # Create Document record
    document = {
        "document_type": document_type,
        "file_path": str(file_path),
        "truck_id": truck_id,
        "driver_id": driver_id,
        "direct_organization_id": direct_organization_id
    }

    
    # document = Document(
    #     document_type=document_type,
    #     file_path=str(file_path),
    #     truck_id=truck_id,
    #     driver_id=driver_id,
    #     direct_organization_id=direct_organization_id,
    # )

    # db.add(document)
    # db.commit()
    # db.refresh(document)
    

    return repo.create(document)
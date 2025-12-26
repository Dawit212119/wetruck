# api/truck_router.py
from datetime import date
from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Query
from typing import Dict, Any, List, Optional
# from sqlalchemy.orm import Session
from src.api.schemas.generic import GenericCUDResponse, GenericResponse
from src.api.schemas.truck import TruckCreate, TruckPaginatedResponse, TruckStatusEnum, TruckTypeEnum, TruckUpdate, TruckRead
# from src.models.models import Truck
from src.core.api_utils import build_filters
from src.domain.enums.document import DocumentTypeEnum
from src.models.models import Truck
from src.repositories.dependencies import get_repository, get_tenant_aware_repository
from src.repositories.document_repository import DocumentRepository
from src.repositories.truck_repository import TruckRepository
# from dependencies import get_db, get_current_organization_id  # your auth/tenant dependency

router = APIRouter()

get_truck_repo = get_tenant_aware_repository(TruckRepository)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_truck(
    req: TruckCreate,
    repo: TruckRepository = Depends(get_truck_repo)
):
    return GenericCUDResponse(
        status=True,
        success_message="Truck created successfully",
        result=TruckRead.model_validate(repo.create(req.model_dump())).model_dump()
    )

@router.get("/{id}", response_model=TruckRead)
def get_truck(
    id: int,
    repo: TruckRepository = Depends(get_truck_repo)
):
    truck = repo.get(id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@router.patch("/{id}")
def update(
    id: int,
    req: TruckUpdate,
    repo: TruckRepository = Depends(get_truck_repo)
):
    update_data = req.model_dump(exclude_unset=True)
    return GenericCUDResponse(
        status=True,
        success_message="Updated successfully",
        result=TruckRead.model_validate(repo.update(id, update_data))
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_truck(
    id: int,
    repo: TruckRepository = Depends(get_truck_repo)
):
    success = repo.soft_delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Truck not found or already deleted")
    return None

@router.get("/", response_model=TruckPaginatedResponse)
def list_trucks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    # Filters - all optional
    status: Optional[TruckStatusEnum] = None,
    truck_type: Optional[TruckTypeEnum] = None,
    vin: Optional[str] = None,
    plate_number: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    color: Optional[str] = None,
    capacity_quintal: Optional[int] = None,
    registration_date: Optional[date] = None,
    gov_id: Optional[str] = None,
    gps_device_id: Optional[int] = None,
    repo: TruckRepository = Depends(get_truck_repo),
):
    filters = build_filters(
        status=status,
        truck_type=truck_type,
        vin=vin,
        plate_number=plate_number,
        make=make,
        model=model,
        year=year,
        color=color,
        capacity_quintal=capacity_quintal,
        registration_date=registration_date,
        gov_id=gov_id,
        gps_device_id=gps_device_id,
    )

    items, total, page, per_page, pages = repo.paginated_list(page=page, per_page=per_page, filters=filters)

    return TruckPaginatedResponse(
        status=True,
        message="Trucks fetched successfully",
        items=items,
        total=total,
        page=page,
        pages=pages,
        per_page=per_page
    )


# Directory to store uploaded files (change to S3 or cloud storage in production)
UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

get_document_repo = get_tenant_aware_repository(DocumentRepository)


@router.post(
    "/{id}/documents",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    status_code=status.HTTP_201_CREATED,
    summary="Upload a single document attached to truck",
)
async def upload_document(
    id: int,
    document_type: DocumentTypeEnum = Form(..., description="Type of the document"),
    file: UploadFile = File(..., description="The document file to upload"),
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: TruckRepository = Depends(get_truck_repo)
):
    truck = repo.get(id = id)
    # Create Document record
    document = {
        "document_type": document_type,
        "file_path": str(await save_on_file(file=file)),
        "truck_id": id,
    }
    return repo_document.create(document)

@router.get(
    "/{id}/documents",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    status_code=status.HTTP_201_CREATED,
    summary="Get document attached to truck",
)
async def get_document(
    id: int,
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: TruckRepository = Depends(get_truck_repo)
):
    truck: Truck = repo.get(id = id)
    return list(filter(lambda doc: not doc.deleted, truck.documents))

@router.delete(
    "/{id}/documents/{document_id}",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Get document attached to truck",
)
async def delete_document(
    id: int,
    document_id: int,
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: TruckRepository = Depends(get_truck_repo)
):
    truck = repo.get(id = id)
    success = repo_document.soft_delete(id = document_id) 
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or already deleted")
    return None

async def save_on_file(file: UploadFile) -> str :
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

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
    
    return file_path
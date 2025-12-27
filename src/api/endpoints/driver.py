from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from src.api.schemas.document import DocumentResponse
from src.api.schemas.driver import DriverCreate, DriverPaginatedResponse, DriverResponse, DriverUpdate
from src.domain.enums.document import DocumentEntityType, DocumentTypeEnum
from src.models.models import Document, Driver
from src.repositories.dependencies import get_tenant_aware_repository
from src.repositories.document_repository import DocumentRepository
from src.repositories.driver_repository import DriverRepository
from src.core.security.dependencies import transporter_only
from src.core.exceptions import CustomHTTPException
from src.api.schemas.generic import GenericCUDResponse
from src.core.api_utils import build_filters
from typing import Optional
from src.services.document import DocumentService

router = APIRouter( dependencies=[Depends(transporter_only)])
get_driver_repo = get_tenant_aware_repository(DriverRepository)
get_document_repo = get_tenant_aware_repository(DocumentRepository)


@router.get("/", response_model=DriverPaginatedResponse)
def list_drivers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    driver_license_number: Optional[str] = None,
    status: Optional[str] = None,
    repo: DriverRepository = Depends(get_driver_repo),
):
    filters = build_filters(
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        email=email,
        driver_license_number=driver_license_number,
        status=status,
    )

    items, total, page, per_page, pages = repo.paginated_list(
        page=page, per_page=per_page, filters=filters
    )

    return DriverPaginatedResponse(
        status=True,
        message="Drivers fetched successfully",
        items=items,
        total=total,
        page=page,
        pages=pages,
        per_page=per_page
    )

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_driver(
    payload: DriverCreate,
    repo: DriverRepository = Depends(get_driver_repo)
):
    if  repo.is_already_exist(
        license_number=payload.driver_license_number,
        phone_number=payload.phone_number,
        email=payload.email
    ):
        raise CustomHTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Driver already exists",
            code="DRIVER_DUPLICATE"
        )

    driver = repo.create(payload.model_dump())
    return GenericCUDResponse(
        status=True,
        success_message="Driver created successfully",
        result=DriverResponse.model_validate(driver)
    )

@router.get("/{id}")
def get_driver(
    id: int,
    repo: DriverRepository = Depends(get_driver_repo)
):
    driver = repo.get(id)
    if not driver:
        raise CustomHTTPException(
            status.HTTP_404_NOT_FOUND,
            "Driver not found",
            code="DRIVER_NOT_FOUND"
        )

    return GenericCUDResponse(
        status=True,
        success_message="Driver retrieved successfully",
        result=DriverResponse.model_validate(driver)
    )

@router.patch("/{id}")
def update_driver(
    id: int,
    req: DriverUpdate,
    repo: DriverRepository = Depends(get_driver_repo)
):
    update_data = req.model_dump(exclude_unset=True)
    return GenericCUDResponse(
        status=True,
        success_message="Updated successfully",
        result=DriverResponse.model_validate(repo.update(id, update_data))
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(
    id: int,
    repo: DriverRepository = Depends(get_driver_repo)
):
    ok =  repo.soft_delete(id)
    if not ok:
        raise CustomHTTPException(
            status.HTTP_404_NOT_FOUND,
            "Driver not found",
            code="DRIVER_NOT_FOUND"
        )

    return  # 204 must not return body




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
    repo: DriverRepository = Depends(get_driver_repo)
):
    driver = repo.get(id = id)
    # Create Document record
    document = {
        "document_type": document_type,
        "file_path": str(await DocumentService.save_on_aws(file=file)),
        "driver_id": id,
        "entity_type": DocumentEntityType.DRIVER
    }
    return repo_document.create(document)

@router.get(
    "/{id}/documents",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    status_code=status.HTTP_201_CREATED,
    summary="Get document attached to driver",
)
async def get_documents(
    id: int,
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: DriverRepository = Depends(get_driver_repo)
):
    driver: Driver = repo.get(id = id)
    return list(filter(lambda doc: not doc.deleted, driver.documents))

@router.get(
    "/{id}/documents/{document_id}",
    response_model=DocumentResponse,  # or a pydantic response model if you prefer
    status_code=status.HTTP_200_OK,
    summary="Get document attached to driver",
)
async def get_document(
    id: int,
    document_id: int,
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: DriverRepository = Depends(get_driver_repo)
):
    truck = repo.get(id = id)
    document = repo_document.get(id = document_id)

    return await DocumentService.to_document_response(doc=document)

@router.patch(
    "{id}/documents/{document_id}",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    summary="Update document",
)
async def update_document(
    id: int,
    document_id: int,
    document_type: Optional[DocumentTypeEnum] = Form(None, description="Type of the document"),
    file: Optional[UploadFile] = File(None, description="The document file to upload"),
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: DriverRepository = Depends(get_driver_repo)
):
    truck = repo.get(id = id)
    document: Document = repo_document.get(id= document_id)
    if file:
        document.file_path = str(await DocumentService.save_on_aws(file=file))
    
    if document_type:
        document.document_type = document_type
    
    repo_document.commit()
    repo_document.refresh(document)
    return document

@router.delete(
    "/{id}/documents/{document_id}",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Get document attached to driver",
)
async def delete_document(
    id: int,
    document_id: int,
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: DriverRepository = Depends(get_driver_repo)
):
    truck = repo.get(id = id)
    success = repo_document.soft_delete(id = document_id) 
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or already deleted")
    return None

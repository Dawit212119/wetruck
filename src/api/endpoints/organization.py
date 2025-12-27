from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.api.schemas.document import DocumentResponse
from src.api.schemas.generic import GenericCUDResponse
from src.api.schemas.organization import OrganizationPaginatedResponse, OrganizationRead, OrganizationCreate, OrganizationUpdate
from src.core.api_utils import build_filters
from src.core.security.dependencies import get_current_user_tenant
from src.domain.enums.document import DocumentEntityType, DocumentTypeEnum
from src.domain.enums.organization import OrganizationTypeEnum
from src.models.models import Document, Organization
from src.repositories.dependencies import get_repository, get_tenant_aware_repository
from src.repositories.document_repository import DocumentRepository
from src.repositories.organization_repository import OrganizationRepository
from src.services.document import DocumentService


router = APIRouter()

get_organization_repo = get_repository(OrganizationRepository)
get_document_repo = get_tenant_aware_repository(DocumentRepository)


@router.post("/", 
            #  response_model=GenericCUDResponse[OrganizationRead],
             status_code=status.HTTP_201_CREATED,
             summary="Create a new organization",
        )
async def create(
        req: OrganizationCreate,
        repo: OrganizationRepository = Depends(get_organization_repo)
):
    return GenericCUDResponse(
        status=True,
        success_message="Created successfully",
        result=OrganizationRead.model_validate(repo.create(req.model_dump()))
    )

@router.get(
    "/",
    response_model=OrganizationPaginatedResponse,
    summary="Get list of organizations",
)
async def list_organization(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    # Filters - all optional
    type: Optional[OrganizationTypeEnum] = None,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[EmailStr] = None,
    repo: OrganizationRepository = Depends(get_organization_repo)
):
    filters = build_filters(type=type, name=name, phone=phone, email=email)
    items, total, page, per_page, pages = repo.paginated_list(page=page, per_page=per_page, filters=filters)

    return OrganizationPaginatedResponse(
        status=True,
        message="Fetched successfully",
        items=items,
        total=total,
        page=page,
        pages=pages,
        per_page=per_page
    )
    

@router.get(
    "/{id}",
    response_model=OrganizationRead,
    summary="Get organization by ID",
)
async def get(
    id: int,
    repo: OrganizationRepository = Depends(get_organization_repo)
):
    return repo.get(id=id)


@router.patch(
    "/{id}",
    # response_model=OrganizationRead,
    summary="Partially update an organization",
)
async def update(
    id: int,
    req: OrganizationUpdate,
    repo: OrganizationRepository = Depends(get_organization_repo)
):
    update_data = req.model_dump(exclude_unset=True)
    return GenericCUDResponse(
        status=True,
        success_message="Updated successfully",
        result=OrganizationRead.model_validate(repo.update(id, update_data))
    )



@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete an organization",
)
async def delete(
    id: int,
    repo: OrganizationRepository = Depends(get_organization_repo)
):
    success = repo.soft_delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found or already deleted")
    return None


@router.post(
    "/documents",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    status_code=status.HTTP_201_CREATED,
    summary="Upload a single document attached to organization for transporter and shipper user type",
)
async def upload_document(
    document_type: DocumentTypeEnum = Form(..., description="Type of the document"),
    file: UploadFile = File(..., description="The document file to upload"),
    organization_id: int = Depends(get_current_user_tenant),
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: OrganizationRepository = Depends(get_organization_repo)
):
    org = repo.get(id = organization_id)
    # Create Document record
    document = {
        "document_type": document_type,
        "file_path": str(await DocumentService.save_on_aws(file=file)),
        "entity_type": DocumentEntityType.ORGANIZATION
    }
    return repo_document.create(document)


@router.get(
    "/documents/list",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    summary="Get document attached to organization",
)
async def list_documents(
    organization_id: int = Depends(get_current_user_tenant),
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: OrganizationRepository = Depends(get_organization_repo)
):
    org: Organization = repo.get(id = organization_id)
    return list(filter(lambda doc: not doc.deleted, org.documents))

@router.get(
    "/documents/{document_id}/get",
    response_model=DocumentResponse,  # or a pydantic response model if you prefer
    status_code=status.HTTP_200_OK,
    summary="Get document attached to Organization",
)
async def get_document(
    document_id: int,
    organization_id: int = Depends(get_current_user_tenant),
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: OrganizationRepository = Depends(get_organization_repo)
):
    org = repo.get(id = organization_id)
    document = repo_document.get(id = document_id)

    return await DocumentService.to_document_response(doc=document)

@router.patch(
    "/documents/{document_id}/update",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    summary="Update document",
)
async def update_document(
    document_id: int,
    document_type: Optional[DocumentTypeEnum] = Form(None, description="Type of the document"),
    file: Optional[UploadFile] = File(None, description="The document file to upload"),
    organization_id: int = Depends(get_current_user_tenant),
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: OrganizationRepository = Depends(get_organization_repo)
):
    org = repo.get(id = organization_id)
    document: Document = repo_document.get(id= document_id)
    if file:
        document.file_path = str(await DocumentService.save_on_aws(file=file))
    
    if document_type:
        document.document_type = document_type
    
    repo_document.commit()
    repo_document.refresh(document)
    return document

@router.delete(
    "/documents/{document_id}/delete",
    # response_model=DocumentResponse,  # or a pydantic response model if you prefer
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Get document attached to Organization",
)
async def delete_document(
    document_id: int,
    organization_id: int = Depends(get_current_user_tenant),
    repo_document: DocumentRepository = Depends(get_document_repo),
    repo: OrganizationRepository = Depends(get_organization_repo)
):
    org = repo.get(id = organization_id)
    success = repo_document.soft_delete(id = document_id) 
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or already deleted")
    return None

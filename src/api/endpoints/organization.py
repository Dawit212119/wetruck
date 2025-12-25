from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.api.schemas.generic import GenericCUDResponse
from src.api.schemas.organization import OrganizationPaginatedResponse, OrganizationRead, OrganizationCreate, OrganizationUpdate
from src.core.api_utils import build_filters
from src.domain.enums.organization import OrganizationTypeEnum
from src.repositories.dependencies import get_repository
from src.repositories.organization_repository import OrganizationRepository


router = APIRouter()

get_organization_repo = get_repository(organization_id=None, repo_cls=OrganizationRepository)


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
async def list(
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

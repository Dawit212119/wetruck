

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.core.security.password import hash_password

from src.api.schemas.user import UserProfileBase, UserRegisterBase, UserRegisterResponse
from src.domain.enums.user import UserStatusEnum, UserTypeEnum
from src.models.models import BackOffice, ShipperUser, TransporterUser, User
from src.repositories.dependencies import get_repository
from src.repositories.organization_repository import OrganizationRepository
from src.repositories.user_repository import UserRepository
from src.repositories.backoffice_repository import BackOfficeUserRepository
from src.repositories.shipper_repository import ShipperUserRepository
from src.repositories.transporter_repository import TransporterUserRepository

router = APIRouter()


get_user_repo = get_repository(organization_id=None, repo_cls=UserRepository)
get_organization_repo = get_repository(organization_id=None, repo_cls=OrganizationRepository)

get_backoffice_user_repo = get_repository(organization_id=None, repo_cls=BackOfficeUserRepository)
get_shipper_user_repo = get_repository(organization_id=None, repo_cls=ShipperUserRepository)
get_transporter_user_repo = get_repository(organization_id=None, repo_cls=TransporterUserRepository)

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    req: UserRegisterBase,
    repo: UserRepository = Depends(get_user_repo),
    repo_org: OrganizationRepository = Depends(get_organization_repo),
    backoffice_user_repo: OrganizationRepository = Depends(get_backoffice_user_repo),
    shipper_user_repo: ShipperUserRepository = Depends(get_shipper_user_repo),
    transporter_user_repo: TransporterUserRepository = Depends(get_transporter_user_repo)
    ):
    
    
    if repo.exists(filters={User.username: req.username, User.email: req.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    if(req.user_type in [UserTypeEnum.SHIPPER, UserTypeEnum.TRANSPORTER] and req.organization_id == None):
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization data missed"
            )
    
    org = repo_org.get(id=req.organization_id) if req.organization_id != None else None
    if req.organization_id != None and not org:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

    # Create base User
    # new_user = User(
    #     username=req.username,
    #     password=hash_password(req.password),
    #     email=req.email,
    #     phone=req.phone,
    #     first_name=req.first_name,
    #     last_name=req.last_name,
    #     user_type=req.user_type,
    #     organization_id=req.organization_id,
    #     status=UserStatusEnum.ACTIVE
    # )

    req.password = hash_password(req.password)

    new_user = repo.create(req.model_dump())
    
    if org:
        new_user.organization = org
        repo.commit()

    # Create the appropriate profile based on user_type
    if req.user_type == UserTypeEnum.TRANSPORTER:
        profile = UserProfileBase(user_id=new_user.id)
        transporter_user_repo.create(profile.model_dump())
    elif req.user_type == UserTypeEnum.SHIPPER:
        profile = UserProfileBase(user_id=new_user.id)
        shipper_user_repo.create(profile.model_dump())
    else:
        profile = UserProfileBase(user_id=new_user.id)
        backoffice_user_repo.create(profile.model_dump())

    return new_user
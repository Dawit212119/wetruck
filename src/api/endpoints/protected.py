from fastapi import APIRouter, Depends

from src.core.security.dependencies import get_current_user, require_roles

router = APIRouter()

@router.get("/me")
def me(user=Depends(get_current_user)):
    # If no/invalid token => 401 happens before entering this function
    return {"sub": user["sub"], "role": user["role"]}

@router.get("/admin-only")
def admin_only(user=Depends(require_roles("admin"))):
    # If token valid but role != admin => 403
    return {"message": "Welcome Admin", "user": user}

@router.get("/cs-or-admin")
def cs_or_admin(user=Depends(require_roles("cs", "admin"))):
    return {"message": "Welcome CS/Admin", "user": user}

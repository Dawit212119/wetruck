from fastapi import HTTPException, status


class InvalidTenantException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing tenant"
        )

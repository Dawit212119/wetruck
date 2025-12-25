from enum import Enum


class UserTypeEnum(Enum):
    BACKOFFICE = "backoffice"
    TRANSPORTER = "transporter"
    SHIPPER = "shipper"
    ADMIN = "admin"
    CUSTOMER_SUPPORT = "cs"


class UserStatusEnum(Enum):
    ACTIVE = "active"
    IN_ACTIVE = "in_active"



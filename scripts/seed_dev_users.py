"""Seed development users and organization."""
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.models.models import User, Organization, BackOffice, TransporterUser, ShipperUser
from src.core.db.session import SessionLocal
from src.core.security.password import hash_password
from src.domain.enums.user import UserTypeEnum, UserStatusEnum
from src.domain.enums.organization import OrganizationTypeEnum


def seed_dev_data():
    """Seed development users and organization."""
    db: Session = SessionLocal()
    
    try:
        # Fix user_type column length if it's too small
        try:
            db.execute(text("""
                ALTER TABLE "user" 
                ALTER COLUMN user_type TYPE VARCHAR(50)
            """))
            db.commit()
            print("Updated user_type column length to 50")
        except Exception as e:
            # Column might already be correct or not exist yet
            db.rollback()
            print(f"Note: Could not alter user_type column: {e}")
        
        # Check if users already exist
        existing_user = db.query(User).first()
        if existing_user:
            print("Users already exist. Skipping seed.")
            db.close()
            return
        
        # Create organization
        org = Organization(
            type=OrganizationTypeEnum.TRANSPORTER,
            name="WeTruck Development",
            email="dev@wetruck.ai",
            phone="+1234567890"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        print(f"Created organization: {org.name} (ID: {org.id})")
        
        # Create users
        users_data = [
            {
                "username": "admin@wetruck.ai",
                "email": "admin@wetruck.ai",
                "password": "admin123",
                "user_type": UserTypeEnum.ADMIN,
                "user_type_value": UserTypeEnum.ADMIN.value,  # Explicitly use enum value
                "first_name": "Admin",
                "last_name": "User",
                "organization_id": None,  # Admin can be org-less
            },
            {
                "username": "cs@wetruck.ai",
                "email": "cs@wetruck.ai",
                "password": "cs123",
                "user_type": UserTypeEnum.CUSTOMER_SUPPORT,
                "user_type_value": UserTypeEnum.CUSTOMER_SUPPORT.value,  # 'cs'
                "first_name": "Customer",
                "last_name": "Support",
                "organization_id": None,  # CS can be org-less
            },
            {
                "username": "shipper@wetruck.ai",
                "email": "shipper@wetruck.ai",
                "password": "shipper123",
                "user_type": UserTypeEnum.SHIPPER,
                "user_type_value": UserTypeEnum.SHIPPER.value,
                "first_name": "Shipper",
                "last_name": "User",
                "organization_id": org.id,
            },
            {
                "username": "transporter@wetruck.ai",
                "email": "transporter@wetruck.ai",
                "password": "transporter123",
                "user_type": UserTypeEnum.TRANSPORTER,
                "user_type_value": UserTypeEnum.TRANSPORTER.value,
                "first_name": "Transporter",
                "last_name": "User",
                "organization_id": org.id,
            },
            {
                "username": "backoffice@wetruck.ai",
                "email": "backoffice@wetruck.ai",
                "password": "backoffice123",
                "user_type": UserTypeEnum.BACKOFFICE,
                "user_type_value": UserTypeEnum.BACKOFFICE.value,
                "first_name": "Backoffice",
                "last_name": "User",
                "organization_id": org.id,
            },
        ]
        
        created_users = []
        for user_data in users_data:
            # Create user with enum objects
            # SQLAlchemy with native_enum=False should convert enum to value string
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                password=hash_password(user_data["password"]),
                user_type=user_data["user_type"],  # Enum object - SQLAlchemy converts to value
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                organization_id=user_data["organization_id"],
                status=UserStatusEnum.ACTIVE,
            )
            db.add(user)
            db.flush()  # Flush to get the user ID
            created_users.append((user, user_data["user_type"]))
            print(f"Created user: {user.username} ({user_data['user_type_value']})")
            db.add(user)
            db.flush()  # Flush to get the user ID
            created_users.append((user, user_data["user_type"]))
            print(f"Created user: {user.username} ({user.user_type.value})")
        
        db.commit()
        
        # Create user profiles based on user_type
        for user, user_type in created_users:
            if user_type == UserTypeEnum.BACKOFFICE:
                profile = BackOffice(user_id=user.id)
                db.add(profile)
                print(f"Created BackOffice profile for {user.username}")
            elif user_type == UserTypeEnum.TRANSPORTER:
                profile = TransporterUser(user_id=user.id)
                db.add(profile)
                print(f"Created TransporterUser profile for {user.username}")
            elif user_type == UserTypeEnum.SHIPPER:
                profile = ShipperUser(user_id=user.id)
                db.add(profile)
                print(f"Created ShipperUser profile for {user.username}")
        
        db.commit()
        
        print("\n" + "="*60)
        print("Development users created successfully!")
        print("="*60)
        print("\nLogin credentials:")
        for user_data in users_data:
            print(f"  {user_data['username']} / {user_data['password']}")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_dev_data()

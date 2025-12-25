"""
Seed script to populate the database with development users and organizations.

This script creates:
- 2 Organizations (1 SHIPPER, 1 TRANSPORTER)
- 5 Users (admin, backoffice, shipper, transporter, customer support)
- Associated user type records (BackOffice, ShipperUser, TransporterUser)
"""

from src.core.db.session import SessionLocal
from src.models.models import User, Organization, BackOffice, ShipperUser, TransporterUser
from src.core.security.password import hash_password
from src.domain.enums.organization import OrganizationTypeEnum
from src.domain.enums.user import UserTypeEnum, UserStatusEnum

def seed_database():
    """Seed the database with development data."""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_user = db.query(User).first()
        if existing_user:
            print("⚠️  Database already seeded. Users already exist.")
            return
        
        print("🌱 Seeding database...")
        
        # Create Organizations
        print("\n📦 Creating organizations...")
        
        shipper_org = Organization(
            type=OrganizationTypeEnum.SHIPPER,
            name="Demo Shipper Inc",
            email="contact@demoshipper.com",
            phone="+1-555-0100"
        )
        
        transporter_org = Organization(
            type=OrganizationTypeEnum.TRANSPORTER,
            name="Fast Transport Ltd",
            email="info@fasttransport.com",
            phone="+1-555-0200"
        )
        
        db.add(shipper_org)
        db.add(transporter_org)
        db.commit()
        db.refresh(shipper_org)
        db.refresh(transporter_org)
        
        print(f"   ✓ Created organization: {shipper_org.name} (ID: {shipper_org.id})")
        print(f"   ✓ Created organization: {transporter_org.name} (ID: {transporter_org.id})")
        
        # Create Users
        print("\n👥 Creating users...")
        
        # Admin User (no organization)
        admin_user = User(
            username="admin@wetruck.ai",
            email="admin@wetruck.ai",
            password=hash_password("admin123"),
            user_type=UserTypeEnum.ADMIN,
            first_name="Admin",
            last_name="User",
            status=UserStatusEnum.ACTIVE,
            organization_id=None
        )
        
        # Backoffice User (no organization)
        backoffice_user = User(
            username="backoffice@wetruck.ai",
            email="backoffice@wetruck.ai",
            password=hash_password("backoffice123"),
            user_type=UserTypeEnum.BACKOFFICE,
            first_name="Back",
            last_name="Office",
            status=UserStatusEnum.ACTIVE,
            organization_id=None
        )
        
        # Customer Support User (no organization)
        cs_user = User(
            username="support@wetruck.ai",
            email="support@wetruck.ai",
            password=hash_password("support123"),
            user_type=UserTypeEnum.CUSTOMER_SUPPORT,
            first_name="Customer",
            last_name="Support",
            status=UserStatusEnum.ACTIVE,
            organization_id=None
        )
        
        # Shipper User (linked to shipper organization)
        shipper_user = User(
            username="shipper@wetruck.ai",
            email="shipper@wetruck.ai",
            password=hash_password("shipper123"),
            user_type=UserTypeEnum.SHIPPER,
            first_name="John",
            last_name="Shipper",
            status=UserStatusEnum.ACTIVE,
            organization_id=shipper_org.id
        )
        
        # Transporter User (linked to transporter organization)
        transporter_user = User(
            username="transporter@wetruck.ai",
            email="transporter@wetruck.ai",
            password=hash_password("transporter123"),
            user_type=UserTypeEnum.TRANSPORTER,
            first_name="Mike",
            last_name="Transporter",
            status=UserStatusEnum.ACTIVE,
            organization_id=transporter_org.id
        )
        
        db.add_all([admin_user, backoffice_user, cs_user, shipper_user, transporter_user])
        db.commit()
        db.refresh(admin_user)
        db.refresh(backoffice_user)
        db.refresh(cs_user)
        db.refresh(shipper_user)
        db.refresh(transporter_user)
        
        print(f"   ✓ Created user: {admin_user.email} (ID: {admin_user.id})")
        print(f"   ✓ Created user: {backoffice_user.email} (ID: {backoffice_user.id})")
        print(f"   ✓ Created user: {cs_user.email} (ID: {cs_user.id})")
        print(f"   ✓ Created user: {shipper_user.email} (ID: {shipper_user.id})")
        print(f"   ✓ Created user: {transporter_user.email} (ID: {transporter_user.id})")
        
        # Create user type associations
        print("\n🔗 Creating user type associations...")
        
        backoffice_record = BackOffice(user_id=backoffice_user.id)
        shipper_record = ShipperUser(user_id=shipper_user.id)
        transporter_record = TransporterUser(user_id=transporter_user.id)
        
        db.add_all([backoffice_record, shipper_record, transporter_record])
        db.commit()
        
        print("   ✓ Created BackOffice record")
        print("   ✓ Created ShipperUser record")
        print("   ✓ Created TransporterUser record")
        
        # Print credentials summary
        print("\n" + "="*60)
        print("✅ Database seeded successfully!")
        print("="*60)
        print("\n📋 Login Credentials:")
        print("-" * 60)
        print("Admin User:")
        print(f"  Email: {admin_user.email}")
        print("  Password: admin123")
        print()
        print("Backoffice User:")
        print(f"  Email: {backoffice_user.email}")
        print("  Password: backoffice123")
        print()
        print("Customer Support:")
        print(f"  Email: {cs_user.email}")
        print("  Password: support123")
        print()
        print("Shipper User:")
        print(f"  Email: {shipper_user.email}")
        print("  Password: shipper123")
        print(f"  Organization: {shipper_org.name}")
        print()
        print("Transporter User:")
        print(f"  Email: {transporter_user.email}")
        print("  Password: transporter123")
        print(f"  Organization: {transporter_org.name}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

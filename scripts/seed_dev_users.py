import asyncio
from datetime import datetime
from sqlalchemy import text
from src.models.models import User, Organization
from src.core.db.session import AsyncSessionLocal
from src.core.security.password import hash_password

async def main():
    async with AsyncSessionLocal() as db:

        # Check if users already exist
        result = await db.execute(text('SELECT 1 FROM "user" LIMIT 1'))
        existing_user = result.scalar()
        if existing_user:
            print("Users already exist")
            return

        # Create an organization
        org = Organization(type="internal")
        db.add(org)
        await db.commit()
        await db.refresh(org)

        # Add default users with all fields
        users = [
            User(
                organization_id=org.id,
                user_type="admin",
                username="admin@wetruck.ai",
                password=hash_password("admin123"),
                email="admin@wetruck.ai",
                phone="+251900000001",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                first_name="Admin",
                last_name="User",
                status="active",
            ),
            User(
                organization_id=org.id,
                user_type="shipper",
                username="shipper@wetruck.ai",
                password=hash_password("shipper123"),
                email="shipper@wetruck.ai",
                phone="+251900000002",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                first_name="Shipper",
                last_name="User",
                status="active",
            ),
            User(
                organization_id=org.id,
                user_type="transporter",
                username="transporter@wetruck.ai",
                password=hash_password("transporter123"),
                email="transporter@wetruck.ai",
                phone="+251900000003",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                first_name="Transporter",
                last_name="User",
                status="active",
            ),
        ]

        db.add_all(users)
        await db.commit()

        print("Default users created:")
        print("admin@wetruck.ai / admin123")
        print("shipper@wetruck.ai / shipper123")
        print("transporter@wetruck.ai / transporter123")

# Run the async main function
asyncio.run(main())


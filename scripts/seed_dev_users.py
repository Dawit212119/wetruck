from src.core.db.session import SessionLocal
from src.models.models import User, Organization
from src.core.security.password import hash_password

db = SessionLocal()

existing_user = db.query(User).first()
if existing_user:
    print("Users already exist")
    db.close()
    exit(0)

org = Organization(type="internal")
db.add(org)
db.commit()
db.refresh(org)

users = [
    User(
        username="admin@wetruck.ai",
        password=hash_password("admin123"),
        user_type="admin",
        organization_id=org.id,
    ),
    User(
        username="shipper@wetruck.ai",
        password=hash_password("shipper123"),
        user_type="shipper",
        organization_id=org.id,
    ),
    User(
        username="transporter@wetruck.ai",
        password=hash_password("transporter123"),
        user_type="transporter",
        organization_id=org.id,
    ),
]

db.add_all(users)
db.commit()

print("admin@wetruck.ai / admin123")
print("shipper@wetruck.ai / shipper123")
print("transporter@wetruck.ai / transporter123")

db.close()

"""Check existing GPS devices in database."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def _clean_database_url(url: str) -> str:
    """Remove whitespace and newlines from database URL."""
    return url.strip().replace("\n", "").replace("\r", "")

def get_database_url() -> str:
    """Get database URL from environment."""
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        database_url = _clean_database_url(database_url)
        if "postgresql+asyncpg://" in database_url:
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return database_url
    raise ValueError("DATABASE_URL not found in environment")

def main():
    """Check existing GPS devices."""
    url = get_database_url()
    engine = create_engine(url)
    conn = engine.connect()
    
    try:
        # Check for devices with "string" values
        result = conn.execute(text("""
            SELECT id, external_device_id, imei_number, organization_id, deleted
            FROM gps_device 
            WHERE external_device_id = 'string' OR imei_number = 'string'
        """))
        rows = result.fetchall()
        
        print(f"Found {len(rows)} existing devices with 'string' values:")
        for row in rows:
            print(f"  ID: {row[0]}, external_device_id: {row[1]}, imei_number: {row[2]}, org_id: {row[3]}, deleted: {row[4]}")
        
        # Check all devices
        result = conn.execute(text("SELECT COUNT(*) FROM gps_device"))
        total = result.scalar()
        print(f"\nTotal GPS devices in database: {total}")
        
        # Check constraints
        result = conn.execute(text("""
            SELECT constraint_name, constraint_type 
            FROM information_schema.table_constraints 
            WHERE table_name = 'gps_device' AND constraint_type = 'UNIQUE'
        """))
        constraints = result.fetchall()
        print(f"\nUnique constraints on gps_device:")
        for constraint in constraints:
            print(f"  {constraint[0]} ({constraint[1]})")
            
    finally:
        conn.close()

if __name__ == "__main__":
    main()


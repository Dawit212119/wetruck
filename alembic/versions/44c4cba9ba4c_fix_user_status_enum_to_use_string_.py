"""Fix user status enum values to match Python enum

Revision ID: 44c4cba9ba4c
Revises: aae6c42b0487
Create Date: 2025-12-25 16:28:22.499367

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44c4cba9ba4c'
down_revision: Union[str, Sequence[str], None] = 'aae6c42b0487'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - fix user.status enum values to match Python enum."""
    # The database enum was created with enum names ('ACTIVE', 'IN_ACTIVE')
    # but Python enum has values ('active', 'in_active')
    # We need to update the enum type to have the correct values
    
    # Step 1: Convert existing data from enum names to enum values
    # Also handle any invalid values (like 'suspended') by converting to 'in_active'
    op.execute("""
        UPDATE "user" 
        SET status = CASE 
            WHEN status::text = 'ACTIVE' THEN 'active'
            WHEN status::text = 'IN_ACTIVE' THEN 'in_active'
            WHEN status::text = 'active' THEN 'active'
            WHEN status::text = 'in_active' THEN 'in_active'
            ELSE 'in_active'  -- Convert any other invalid values to 'in_active'
        END
    """)
    
    # Step 2: Drop the default constraint (if exists)
    op.execute("ALTER TABLE \"user\" ALTER COLUMN status DROP DEFAULT")
    
    # Step 3: Temporarily convert column to text
    op.execute("""
        ALTER TABLE "user" 
        ALTER COLUMN status TYPE VARCHAR(50) 
        USING status::text
    """)
    
    # Step 4: Drop the old enum type
    op.execute("DROP TYPE IF EXISTS userstatusenum")
    
    # Step 5: Create the enum type with correct values (matching Python enum values)
    op.execute("CREATE TYPE userstatusenum AS ENUM ('active', 'in_active')")
    
    # Step 6: Convert column back to enum type
    op.execute("""
        ALTER TABLE "user" 
        ALTER COLUMN status TYPE userstatusenum 
        USING status::userstatusenum
    """)
    
    # Step 7: Restore the default value
    op.execute("ALTER TABLE \"user\" ALTER COLUMN status SET DEFAULT 'active'::userstatusenum")


def downgrade() -> None:
    """Downgrade schema - revert to old enum values."""
    # Convert data back to enum names
    op.execute("""
        UPDATE "user" 
        SET status = CASE 
            WHEN status::text = 'active' THEN 'ACTIVE'
            WHEN status::text = 'in_active' THEN 'IN_ACTIVE'
            ELSE status::text
        END
    """)
    
    # Convert to text
    op.execute("""
        ALTER TABLE "user" 
        ALTER COLUMN status TYPE VARCHAR(50) 
        USING status::text
    """)
    
    # Drop enum
    op.execute("DROP TYPE IF EXISTS userstatusenum")
    
    # Recreate with old values
    op.execute("CREATE TYPE userstatusenum AS ENUM ('ACTIVE', 'IN_ACTIVE')")
    
    # Convert back to enum
    op.execute("""
        ALTER TABLE "user" 
        ALTER COLUMN status TYPE userstatusenum 
        USING status::userstatusenum
    """)

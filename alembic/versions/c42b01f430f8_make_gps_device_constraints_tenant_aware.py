"""Make GPS device constraints tenant-aware

Revision ID: c42b01f430f8
Revises: 2359dc948da9
Create Date: 2025-12-25 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c42b01f430f8'
down_revision: Union[str, Sequence[str], None] = '2359dc948da9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - make GPS device constraints tenant-aware."""
    # Drop existing global unique indexes
    try:
        op.drop_index('ix_gps_device_external_device_id', table_name='gps_device')
    except Exception:
        pass  # Index might not exist
    
    try:
        op.drop_index('ix_gps_device_imei_number', table_name='gps_device')
    except Exception:
        pass  # Index might not exist
    
    # Create non-unique indexes for performance
    op.create_index('ix_gps_device_external_device_id', 'gps_device', ['external_device_id'])
    op.create_index('ix_gps_device_imei_number', 'gps_device', ['imei_number'])
    
    # Create tenant-aware unique constraints (unique per organization)
    op.create_unique_constraint(
        'uq_gps_device_org_external_id',
        'gps_device',
        ['organization_id', 'external_device_id']
    )
    op.create_unique_constraint(
        'uq_gps_device_org_imei',
        'gps_device',
        ['organization_id', 'imei_number']
    )


def downgrade() -> None:
    """Downgrade schema - revert to global unique constraints."""
    # Drop tenant-aware constraints
    op.drop_constraint('uq_gps_device_org_imei', 'gps_device', type_='unique')
    op.drop_constraint('uq_gps_device_org_external_id', 'gps_device', type_='unique')
    
    # Drop non-unique indexes
    op.drop_index('ix_gps_device_imei_number', table_name='gps_device')
    op.drop_index('ix_gps_device_external_device_id', table_name='gps_device')
    
    # Recreate global unique indexes
    op.create_index('ix_gps_device_external_device_id', 'gps_device', ['external_device_id'], unique=True)
    op.create_index('ix_gps_device_imei_number', 'gps_device', ['imei_number'], unique=True)

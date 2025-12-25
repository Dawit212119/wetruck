"""Add GPS device fields

Revision ID: 0eebe507824a
Revises: cc1ab75ef35f
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0eebe507824a'
down_revision: Union[str, Sequence[str], None] = 'cc1ab75ef35f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add GPS device specific fields
    # Note: deleted column already exists from previous migration (882727a99327)
    op.add_column('gps_device', sa.Column('external_device_id', sa.String(length=255), nullable=False))
    op.add_column('gps_device', sa.Column('imei_number', sa.String(length=50), nullable=False))
    op.add_column('gps_device', sa.Column('device_name', sa.String(length=255), nullable=True))
    op.add_column('gps_device', sa.Column('device_model', sa.String(length=255), nullable=True))
    op.add_column('gps_device', sa.Column('expire_date', sa.DateTime(timezone=True), nullable=False))
    op.add_column('gps_device', sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False))
    op.add_column('gps_device', sa.Column('status', sa.Boolean(), nullable=True, server_default=sa.text('true')))
    
    # Create unique constraints and indexes
    op.create_index(op.f('ix_gps_device_external_device_id'), 'gps_device', ['external_device_id'], unique=True)
    op.create_index(op.f('ix_gps_device_imei_number'), 'gps_device', ['imei_number'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_gps_device_imei_number'), table_name='gps_device')
    op.drop_index(op.f('ix_gps_device_external_device_id'), table_name='gps_device')
    
    # Drop columns
    op.drop_column('gps_device', 'status')
    op.drop_column('gps_device', 'last_synced_at')
    op.drop_column('gps_device', 'expire_date')
    op.drop_column('gps_device', 'device_model')
    op.drop_column('gps_device', 'device_name')
    op.drop_column('gps_device', 'imei_number')
    op.drop_column('gps_device', 'external_device_id')


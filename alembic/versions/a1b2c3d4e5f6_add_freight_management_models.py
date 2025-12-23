"""Add freight management models (Ship, ShipItem, Truck, Driver, etc.)

Revision ID: a1b2c3d4e5f6
Revises: 773f55cdbd8f
Create Date: 2025-12-23 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '773f55cdbd8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add freight management tables."""
    # Create base tables first (no dependencies)
    op.create_table('gps_device',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('truck',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('gps_device_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['gps_device_id'], ['gps_device.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('driver',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('container',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('price_quote',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create ship table (depends on organization)
    op.create_table('ship',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('shipper_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['shipper_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create ship_item table (depends on ship, truck, driver, container, organization)
    op.create_table('ship_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('ship_id', sa.Integer(), nullable=False),
    sa.Column('truck_id', sa.Integer(), nullable=True),
    sa.Column('driver_id', sa.Integer(), nullable=True),
    sa.Column('container_id', sa.Integer(), nullable=True),
    sa.Column('transporter_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['ship_id'], ['ship.id'], ),
    sa.ForeignKeyConstraint(['truck_id'], ['truck.id'], ),
    sa.ForeignKeyConstraint(['driver_id'], ['driver.id'], ),
    sa.ForeignKeyConstraint(['container_id'], ['container.id'], ),
    sa.ForeignKeyConstraint(['transporter_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create ship_document table (depends on ship)
    op.create_table('ship_document',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ship_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['ship_id'], ['ship.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create ship_item_document table (depends on ship_item)
    op.create_table('ship_item_document',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('ship_item_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['ship_item_id'], ['ship_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create location_log table (depends on ship_item)
    op.create_table('location_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('ship_item_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['ship_item_id'], ['ship_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create payment table (depends on ship_item)
    op.create_table('payment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('ship_item_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['ship_item_id'], ['ship_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create document table (depends on truck, driver, organization)
    op.create_table('document',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('document_type', sa.String(), nullable=True),
    sa.Column('file_path', sa.String(), nullable=False),
    sa.Column('truck_id', sa.Integer(), nullable=True),
    sa.Column('driver_id', sa.Integer(), nullable=True),
    sa.Column('direct_organization_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['truck_id'], ['truck.id'], ),
    sa.ForeignKeyConstraint(['driver_id'], ['driver.id'], ),
    sa.ForeignKeyConstraint(['direct_organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Remove freight management tables."""
    op.drop_table('document')
    op.drop_table('payment')
    op.drop_table('location_log')
    op.drop_table('ship_item_document')
    op.drop_table('ship_document')
    op.drop_table('ship_item')
    op.drop_table('ship')
    op.drop_table('price_quote')
    op.drop_table('container')
    op.drop_table('driver')
    op.drop_table('truck')
    op.drop_table('gps_device')



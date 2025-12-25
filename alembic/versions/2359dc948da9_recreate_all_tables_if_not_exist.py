"""Recreate all tables if not exist

Revision ID: 2359dc948da9
Revises: 44c4cba9ba4c
Create Date: 2025-12-25 16:39:15.097581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '2359dc948da9'
down_revision: Union[str, Sequence[str], None] = '44c4cba9ba4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    conn = op.get_bind()
    result = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}'
        );
    """))
    return result.scalar()


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    result = conn.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}' 
            AND column_name = '{column_name}'
        );
    """))
    return result.scalar()


def upgrade() -> None:
    """Upgrade schema - create all tables if they don't exist."""
    conn = op.get_bind()
    
    # Create enum types if they don't exist
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE organizationtypeenum AS ENUM ('shipper', 'transporter');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE usertypeenum AS ENUM ('backoffice', 'transporter', 'shipper', 'admin', 'cs');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE userstatusenum AS ENUM ('active', 'in_active');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE truckstatusenum AS ENUM ('active', 'inactive', 'maintenance', 'out_of_service');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE trucktypeenum AS ENUM ('flatbed', 'trailer');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    conn.execute(text("""
        DO $$ BEGIN
            CREATE TYPE driverstatusenum AS ENUM ('active', 'suspended');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Create organization table
    if not _table_exists('organization'):
        op.create_table('organization',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('type', sa.Enum('shipper', 'transporter', name='organizationtypeenum', native_enum=False), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=True),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('phone', sa.String(length=50), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create user table
    if not _table_exists('user'):
        op.create_table('user',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('user_type', sa.Enum('backoffice', 'transporter', 'shipper', 'admin', 'cs', name='usertypeenum', native_enum=False), nullable=False),
            sa.Column('username', sa.String(length=255), nullable=False),
            sa.Column('password', sa.String(length=255), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('phone', sa.String(length=20), nullable=True),
            sa.Column('first_name', sa.String(length=100), nullable=True),
            sa.Column('last_name', sa.String(length=100), nullable=True),
            sa.Column('status', sa.Enum('active', 'in_active', name='userstatusenum', native_enum=False), nullable=False, server_default=sa.text("'active'::userstatusenum")),
            sa.Column('organization_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('username'),
            sa.UniqueConstraint('email')
        )
    else:
        # Add missing columns if table exists
        if not _column_exists('user', 'deleted'):
            op.add_column('user', sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        if not _column_exists('user', 'email'):
            op.add_column('user', sa.Column('email', sa.String(length=255), nullable=False))
        if not _column_exists('user', 'phone'):
            op.add_column('user', sa.Column('phone', sa.String(length=20), nullable=True))
        if not _column_exists('user', 'first_name'):
            op.add_column('user', sa.Column('first_name', sa.String(length=100), nullable=True))
        if not _column_exists('user', 'last_name'):
            op.add_column('user', sa.Column('last_name', sa.String(length=100), nullable=True))
        if not _column_exists('user', 'status'):
            op.add_column('user', sa.Column('status', sa.Enum('active', 'in_active', name='userstatusenum', native_enum=False), nullable=False, server_default=sa.text("'active'::userstatusenum")))
    
    # Create user profile tables
    if not _table_exists('backoffice_user'):
        op.create_table('backoffice_user',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('user_id')
        )
    
    if not _table_exists('transporter_user'):
        op.create_table('transporter_user',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('user_id')
        )
    
    if not _table_exists('shipper_user'):
        op.create_table('shipper_user',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('user_id')
        )
    
    # Create driver table
    if not _table_exists('driver'):
        op.create_table('driver',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('first_name', sa.String(length=100), nullable=True),
            sa.Column('last_name', sa.String(length=100), nullable=True),
            sa.Column('phone_number', sa.String(length=20), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('driver_license_number', sa.String(length=100), nullable=False),
            sa.Column('status', sa.Enum('active', 'suspended', name='driverstatusenum', native_enum=False), nullable=False, server_default=sa.text("'active'::driverstatusenum")),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('phone_number'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('driver_license_number')
        )
    
    # Create container table
    if not _table_exists('container'):
        op.create_table('container',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create GPS device table
    if not _table_exists('gps_device'):
        op.create_table('gps_device',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('external_device_id', sa.String(length=255), nullable=False),
            sa.Column('imei_number', sa.String(length=50), nullable=False),
            sa.Column('device_name', sa.String(length=255), nullable=True),
            sa.Column('device_model', sa.String(length=255), nullable=True),
            sa.Column('expire_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('status', sa.Boolean(), nullable=True, server_default=sa.text('true')),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
            sa.PrimaryKeyConstraint('id'),
            # Tenant-aware unique constraints (unique per organization)
            sa.UniqueConstraint('organization_id', 'external_device_id', name='uq_gps_device_org_external_id'),
            sa.UniqueConstraint('organization_id', 'imei_number', name='uq_gps_device_org_imei')
        )
        # Create non-unique indexes for performance
        op.create_index('ix_gps_device_external_device_id', 'gps_device', ['external_device_id'])
        op.create_index('ix_gps_device_imei_number', 'gps_device', ['imei_number'])
    else:
        # Add missing GPS device columns
        for col_name, col_def in [
            ('external_device_id', sa.Column('external_device_id', sa.String(length=255), nullable=False)),
            ('imei_number', sa.Column('imei_number', sa.String(length=50), nullable=False)),
            ('device_name', sa.Column('device_name', sa.String(length=255), nullable=True)),
            ('device_model', sa.Column('device_model', sa.String(length=255), nullable=True)),
            ('expire_date', sa.Column('expire_date', sa.DateTime(timezone=True), nullable=False)),
            ('last_synced_at', sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=False)),
            ('status', sa.Column('status', sa.Boolean(), nullable=True, server_default=sa.text('true'))),
        ]:
            if not _column_exists('gps_device', col_name):
                op.add_column('gps_device', col_def)
        
        # Create indexes if they don't exist (non-unique for performance)
        try:
            op.create_index('ix_gps_device_external_device_id', 'gps_device', ['external_device_id'])
        except:
            pass
        try:
            op.create_index('ix_gps_device_imei_number', 'gps_device', ['imei_number'])
        except:
            pass
        
        # Create tenant-aware unique constraints if they don't exist
        try:
            op.create_unique_constraint('uq_gps_device_org_external_id', 'gps_device', ['organization_id', 'external_device_id'])
        except:
            pass
        try:
            op.create_unique_constraint('uq_gps_device_org_imei', 'gps_device', ['organization_id', 'imei_number'])
        except:
            pass
    
    # Create truck table
    if not _table_exists('truck'):
        op.create_table('truck',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('gps_device_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.Enum('active', 'inactive', 'maintenance', 'out_of_service', name='truckstatusenum', native_enum=False), nullable=False, server_default=sa.text("'inactive'::truckstatusenum")),
            sa.Column('truck_type', sa.Enum('flatbed', 'trailer', name='trucktypeenum', native_enum=False), nullable=False),
            sa.Column('vin', sa.String(length=17), nullable=False),
            sa.Column('plate_number', sa.String(length=20), nullable=False),
            sa.Column('registration_date', sa.Date(), nullable=False),
            sa.Column('gov_id', sa.String(length=50), nullable=True),
            sa.Column('make', sa.String(length=100), nullable=True),
            sa.Column('model', sa.String(length=100), nullable=True),
            sa.Column('year', sa.Integer(), nullable=True),
            sa.Column('color', sa.String(length=50), nullable=True),
            sa.Column('capacity_quintal', sa.Integer(), nullable=False),
            sa.Column('libre_key', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
            sa.ForeignKeyConstraint(['gps_device_id'], ['gps_device.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_truck_vin', 'truck', ['vin'], unique=True)
        op.create_index('ix_truck_plate_number', 'truck', ['plate_number'], unique=True)
    
    # Create document table
    if not _table_exists('document'):
        op.create_table('document',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
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
    
    # Create ship table
    if not _table_exists('ship'):
        op.create_table('ship',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('shipper_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
            sa.ForeignKeyConstraint(['shipper_id'], ['organization.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create ship_item table
    if not _table_exists('ship_item'):
        op.create_table('ship_item',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
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
    
    # Create ship_document table
    if not _table_exists('ship_document'):
        op.create_table('ship_document',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('ship_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['ship_id'], ['ship.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create ship_item_document table
    if not _table_exists('ship_item_document'):
        op.create_table('ship_item_document',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('ship_item_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
            sa.ForeignKeyConstraint(['ship_item_id'], ['ship_item.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create location_log table
    if not _table_exists('location_log'):
        op.create_table('location_log',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('ship_item_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
            sa.ForeignKeyConstraint(['ship_item_id'], ['ship_item.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create payment table
    if not _table_exists('payment'):
        op.create_table('payment',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.Column('ship_item_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
            sa.ForeignKeyConstraint(['ship_item_id'], ['ship_item.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create price_quote table
    if not _table_exists('price_quote'):
        op.create_table('price_quote',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('organization_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order of dependencies
    op.drop_table('price_quote')
    op.drop_table('payment')
    op.drop_table('location_log')
    op.drop_table('ship_item_document')
    op.drop_table('ship_document')
    op.drop_table('ship_item')
    op.drop_table('ship')
    op.drop_table('document')
    op.drop_table('truck')
    op.drop_table('gps_device')
    op.drop_table('container')
    op.drop_table('driver')
    op.drop_table('shipper_user')
    op.drop_table('transporter_user')
    op.drop_table('backoffice_user')
    op.drop_table('user')
    op.drop_table('organization')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS driverstatusenum")
    op.execute("DROP TYPE IF EXISTS trucktypeenum")
    op.execute("DROP TYPE IF EXISTS truckstatusenum")
    op.execute("DROP TYPE IF EXISTS userstatusenum")
    op.execute("DROP TYPE IF EXISTS usertypeenum")
    op.execute("DROP TYPE IF EXISTS organizationtypeenum")

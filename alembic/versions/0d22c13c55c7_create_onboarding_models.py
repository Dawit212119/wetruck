"""Create onboarding models

Revision ID: 0d22c13c55c7
Revises: 1b96914bd5ad
Create Date: 2025-12-23 11:56:15.926637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0d22c13c55c7'
down_revision: Union[str, Sequence[str], None] = '1b96914bd5ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - drop old tables and create new onboarding models."""
    # Drop old tables first (in reverse dependency order - drop dependents first)
    op.execute('DROP TABLE IF EXISTS ship_item_document CASCADE')
    op.execute('DROP TABLE IF EXISTS location_log CASCADE')
    op.execute('DROP TABLE IF EXISTS payment CASCADE')
    op.execute('DROP TABLE IF EXISTS ship_document CASCADE')
    op.execute('DROP TABLE IF EXISTS transporter_user CASCADE')
    op.execute('DROP TABLE IF EXISTS shipper_user CASCADE')
    op.execute('DROP TABLE IF EXISTS backoffice CASCADE')
    op.execute('DROP TABLE IF EXISTS document CASCADE')
    op.execute('DROP TABLE IF EXISTS ship_item CASCADE')
    op.execute('DROP TABLE IF EXISTS truck CASCADE')
    op.execute('DROP TABLE IF EXISTS driver CASCADE')
    op.execute('DROP TABLE IF EXISTS container CASCADE')
    op.execute('DROP TABLE IF EXISTS ship CASCADE')
    op.execute('DROP TABLE IF EXISTS price_quote CASCADE')
    op.execute('DROP TABLE IF EXISTS gps_device CASCADE')
    op.execute('DROP TABLE IF EXISTS org_user CASCADE')
    op.execute('DROP TABLE IF EXISTS onboarding_steps CASCADE')
    op.execute('DROP TABLE IF EXISTS "user" CASCADE')
    op.execute('DROP TABLE IF EXISTS organization CASCADE')
    
    # Create new tables
    op.create_table('organization',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('company_email', sa.String(length=255), nullable=True),
    sa.Column('company_phone', sa.String(length=50), nullable=True),
    sa.Column('onboarding_status', sa.String(length=50), nullable=False, server_default='in_progress'),
    sa.Column('onboarding_step', sa.String(length=50), nullable=True),
    sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('user_type', sa.String(length=50), nullable=False),
    sa.Column('username', sa.String(length=255), nullable=False),
    sa.Column('password', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username'),
    sa.UniqueConstraint('email')
    )
    
    op.create_table('org_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('onboarding_steps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.Column('current_step', sa.String(length=50), nullable=True),
    sa.Column('completed_steps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('step_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False, server_default='in_progress'),
    sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema - drop new tables."""
    op.drop_table('onboarding_steps')
    op.drop_table('org_user')
    op.drop_table('user')
    op.drop_table('organization')

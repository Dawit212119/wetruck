"""Add system_config table and extend user model for admin/CS users

Revision ID: 773f55cdbd8f
Revises: 0d22c13c55c7
Create Date: 2025-12-23 12:17:42.184205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '773f55cdbd8f'
down_revision: Union[str, Sequence[str], None] = '0d22c13c55c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add system_config table and extend user table."""
    # Add new columns to user table
    op.add_column('user', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('user', sa.Column('last_name', sa.String(length=100), nullable=True))
    op.add_column('user', sa.Column('status', sa.String(length=50), server_default='active', nullable=False))
    
    # Create system_config table
    op.create_table('system_config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('config_key', sa.String(length=255), nullable=False),
    sa.Column('config_value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('version', sa.Integer(), server_default='1', nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('config_key')
    )


def downgrade() -> None:
    """Downgrade schema - remove system_config table and user extensions."""
    op.drop_table('system_config')
    op.drop_column('user', 'status')
    op.drop_column('user', 'last_name')
    op.drop_column('user', 'first_name')

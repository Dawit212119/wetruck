"""Make user.organization_id nullable and remove tenant mixin

Revision ID: cc1ab75ef35f
Revises: 7405a09625c3
Create Date: 2025-12-24 22:49:47.120629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc1ab75ef35f'
down_revision: Union[str, Sequence[str], None] = '7405a09625c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "user",
        "organization_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "user",
        "organization_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

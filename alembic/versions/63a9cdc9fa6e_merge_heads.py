"""merge heads

Revision ID: 63a9cdc9fa6e
Revises: 882727a99327, a1b2c3d4e5f6
Create Date: 2025-12-24 12:15:59.495280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63a9cdc9fa6e'
down_revision: Union[str, Sequence[str], None] = ('882727a99327', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

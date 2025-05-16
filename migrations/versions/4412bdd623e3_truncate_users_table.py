"""truncate users table

Revision ID: 4412bdd623e3
Revises: 64a545fba331
Create Date: 2025-04-15 01:36:08.527419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4412bdd623e3'
down_revision: Union[str, None] = '64a545fba331'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute('TRUNCATE TABLE users RESTART IDENTITY CASCADE;')
    pass


def downgrade():
    """Downgrade schema."""
    pass

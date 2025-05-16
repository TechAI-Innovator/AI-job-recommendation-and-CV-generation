"""Replace full_name with surname, middle_name, first_name

Revision ID: 87d0ec53115b
Revises: 4412bdd623e3
Create Date: 2025-04-18 03:29:31.439618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87d0ec53115b'
down_revision: Union[str, None] = '4412bdd623e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Remove full_name column
    op.drop_column('users', 'full_name')

    # Add new columns
    op.add_column('users', sa.Column('surname', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('middle_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('first_name', sa.String(length=100), nullable=True))

def downgrade():
    # Revert changes
    op.add_column('users', sa.Column('full_name', sa.String(length=100), nullable=True))
    op.drop_column('users', 'surname')
    op.drop_column('users', 'middle_name')
    op.drop_column('users', 'first_name')


"""Add code column to specialties table

Revision ID: 002
Revises: 001
Create Date: 2024-02-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add code column to specialties table
    op.add_column('specialties', sa.Column('code', sa.String(length=50), nullable=True))

    # Add index for spo_id on specialties if not exists
    try:
        op.create_index(op.f('ix_specialties_spo_id'), 'specialties', ['spo_id'], unique=False)
    except:
        pass  # Index may already exist


def downgrade() -> None:
    try:
        op.drop_index(op.f('ix_specialties_spo_id'), table_name='specialties')
    except:
        pass
    op.drop_column('specialties', 'code')

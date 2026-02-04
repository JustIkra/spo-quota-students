"""Update students table columns to match model

Revision ID: 003
Revises: 002
Create Date: 2024-02-04 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename attestat_number to certificate_number
    op.alter_column('students', 'attestat_number', new_column_name='certificate_number')

    # Rename full_name to last_name temporarily (we'll split it)
    op.alter_column('students', 'full_name', new_column_name='last_name')

    # Add first_name and middle_name columns
    op.add_column('students', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('students', sa.Column('middle_name', sa.String(length=100), nullable=True))

    # Update existing records - set first_name to last_name (temporary fix)
    op.execute("UPDATE students SET first_name = 'Имя' WHERE first_name IS NULL")

    # Make first_name NOT NULL
    op.alter_column('students', 'first_name', nullable=False)

    # Update index
    try:
        op.drop_index('ix_students_attestat_number', table_name='students')
    except:
        pass
    op.create_index('ix_students_certificate_number', 'students', ['certificate_number'], unique=True)


def downgrade() -> None:
    # Revert index
    try:
        op.drop_index('ix_students_certificate_number', table_name='students')
    except:
        pass
    op.create_index('ix_students_attestat_number', 'students', ['attestat_number'], unique=True)

    # Drop new columns
    op.drop_column('students', 'middle_name')
    op.drop_column('students', 'first_name')

    # Rename columns back
    op.alter_column('students', 'last_name', new_column_name='full_name')
    op.alter_column('students', 'certificate_number', new_column_name='attestat_number')

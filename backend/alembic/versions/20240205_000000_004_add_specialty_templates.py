"""Add specialty templates and one operator per SPO

Revision ID: 004
Revises: 003
Create Date: 2024-02-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get connection for checking existing objects
    connection = op.get_bind()

    # 1. Create specialty_templates table if not exists
    result = connection.execute(
        sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'specialty_templates')")
    )
    if not result.fetchone()[0]:
        op.create_table(
            'specialty_templates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_specialty_templates_id', 'specialty_templates', ['id'], unique=False)
        op.create_index('ix_specialty_templates_code', 'specialty_templates', ['code'], unique=True)

    # 2. Add template_id column to specialties if not exists
    result = connection.execute(
        sa.text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'specialties' AND column_name = 'template_id')")
    )
    if not result.fetchone()[0]:
        op.add_column('specialties', sa.Column('template_id', sa.Integer(), nullable=True))
        op.create_index('ix_specialties_template_id', 'specialties', ['template_id'], unique=False)
        op.create_foreign_key(
            'fk_specialties_template_id',
            'specialties', 'specialty_templates',
            ['template_id'], ['id'],
            ondelete='CASCADE'
        )

    # 3. Add unique constraint on (spo_id, template_id) for specialties if not exists
    result = connection.execute(
        sa.text("SELECT EXISTS (SELECT FROM information_schema.table_constraints WHERE constraint_name = 'uq_specialty_spo_template')")
    )
    if not result.fetchone()[0]:
        op.create_unique_constraint('uq_specialty_spo_template', 'specialties', ['spo_id', 'template_id'])

    # 4. Migrate existing data: create templates from existing specialties
    # Get connection for data migration
    connection = op.get_bind()

    # Find unique (code, name) pairs
    existing_specialties = connection.execute(
        sa.text("SELECT DISTINCT code, name FROM specialties WHERE code IS NOT NULL")
    ).fetchall()

    # Create templates and update specialties
    for code, name in existing_specialties:
        # Insert template
        result = connection.execute(
            sa.text(
                "INSERT INTO specialty_templates (code, name, created_at) "
                "VALUES (:code, :name, NOW()) RETURNING id"
            ),
            {"code": code, "name": name}
        )
        template_id = result.fetchone()[0]

        # Update specialties to link to template
        connection.execute(
            sa.text(
                "UPDATE specialties SET template_id = :template_id "
                "WHERE code = :code AND name = :name"
            ),
            {"template_id": template_id, "code": code, "name": name}
        )

    # 5. Remove duplicate operators per SPO (keep first created)
    # Find SPOs with multiple operators
    duplicates = connection.execute(
        sa.text(
            "SELECT spo_id, array_agg(id ORDER BY created_at) as ids "
            "FROM users WHERE role = 'operator' AND spo_id IS NOT NULL "
            "GROUP BY spo_id HAVING COUNT(*) > 1"
        )
    ).fetchall()

    for spo_id, ids in duplicates:
        # Keep first (oldest), delete rest
        ids_to_delete = ids[1:]  # Skip first
        if ids_to_delete:
            connection.execute(
                sa.text("DELETE FROM users WHERE id = ANY(:ids)"),
                {"ids": ids_to_delete}
            )

    # 6. Add partial unique index on users.spo_id for operators only
    # Note: This is PostgreSQL-specific syntax
    result = connection.execute(
        sa.text("SELECT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'ix_users_spo_id_unique_operator')")
    )
    if not result.fetchone()[0]:
        op.execute(
            "CREATE UNIQUE INDEX ix_users_spo_id_unique_operator "
            "ON users (spo_id) WHERE role = 'OPERATOR'::userrole"
        )


def downgrade() -> None:
    # Remove unique index for operators
    op.execute("DROP INDEX IF EXISTS ix_users_spo_id_unique_operator")

    # Remove unique constraint
    op.drop_constraint('uq_specialty_spo_template', 'specialties', type_='unique')

    # Remove foreign key and column from specialties
    op.drop_constraint('fk_specialties_template_id', 'specialties', type_='foreignkey')
    op.drop_index('ix_specialties_template_id', table_name='specialties')
    op.drop_column('specialties', 'template_id')

    # Drop specialty_templates table
    op.drop_index('ix_specialty_templates_code', table_name='specialty_templates')
    op.drop_index('ix_specialty_templates_id', table_name='specialty_templates')
    op.drop_table('specialty_templates')

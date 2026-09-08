"""responsavel da instituicao

Revision ID: b7e4c2f19a03
Revises: f3a9c1d47e20
Create Date: 2026-09-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7e4c2f19a03'
down_revision = 'f3a9c1d47e20'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_owner', sa.Boolean(), nullable=False, server_default=sa.false())
        )

    # Marca como responsável o usuário mais antigo de cada instituição.
    op.execute(
        """
        UPDATE users SET is_owner = true
        WHERE id IN (
            SELECT DISTINCT ON (organization_id) id
            FROM users
            ORDER BY organization_id, created_at, id
        )
        """
    )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_owner')

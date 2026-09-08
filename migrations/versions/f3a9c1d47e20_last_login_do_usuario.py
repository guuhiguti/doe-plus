"""last login do usuario

Revision ID: f3a9c1d47e20
Revises: d76e8cf2f410
Create Date: 2026-09-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a9c1d47e20'
down_revision = 'd76e8cf2f410'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_login_at')

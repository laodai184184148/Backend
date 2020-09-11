"""create account table

Revision ID: 4261e37546d8
Revises: 
Create Date: 2020-08-31 09:04:26.838471

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4261e37546d8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'account',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Unicode(200)),
    )


def downgrade():
    op.drop_table('account')

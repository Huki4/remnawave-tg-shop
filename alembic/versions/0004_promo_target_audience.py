"""add target_audience to promo_codes

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-10
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('promo_codes',
        sa.Column('target_audience', sa.String(), nullable=False, server_default='all')
    )


def downgrade():
    op.drop_column('promo_codes', 'target_audience')

"""add gifts table

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'gifts',
        sa.Column('gift_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('buyer_id', sa.BigInteger(), sa.ForeignKey('users.user_id'), nullable=False, index=True),
        sa.Column('plan', sa.String(), nullable=False),
        sa.Column('months', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(32), nullable=False, unique=True, index=True),
        sa.Column('is_used', sa.Boolean(), default=False, index=True),
        sa.Column('activated_by_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table('gifts')

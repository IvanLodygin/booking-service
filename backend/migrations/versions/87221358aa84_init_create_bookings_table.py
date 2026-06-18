"""init_create_bookings_table

Revision ID: 87221358aa84
Revises: 
Create Date: 2026-06-16 21:05:08.441603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '87221358aa84'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bookings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('service_type', sa.String(length=255), nullable=False),
        sa.Column('datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'status',
            sa.Enum('pending', 'confirmed', 'failed', name='bookingstatus'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_bookings_status'), 'bookings', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_bookings_status'), table_name='bookings')
    op.drop_table('bookings')
    op.execute("DROP TYPE IF EXISTS bookingstatus")

"""order_number unique per company

Revision ID: 3e89efe30105
Revises: 885f034e93c2
Create Date: 2026-07-17 21:40:56.203776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e89efe30105'
down_revision: Union[str, Sequence[str], None] = '885f034e93c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_index(op.f('ix_service_orders_order_number'), table_name='service_orders')
    op.create_index(
        'ix_service_orders_order_number',
        'service_orders',
        ['order_number'],
        unique=False,
    )
    op.create_unique_constraint(
        'uq_service_orders_company_order_number',
        'service_orders',
        ['company_id', 'order_number'],
    )


def downgrade():
    op.drop_constraint(
        'uq_service_orders_company_order_number',
        'service_orders',
        type_='unique',
    )
    op.drop_index('ix_service_orders_order_number', table_name='service_orders')
    op.create_index(
        op.f('ix_service_orders_order_number'),
        'service_orders',
        ['order_number'],
        unique=True,
    )

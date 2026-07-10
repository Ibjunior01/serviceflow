"""order_number varchar to integer

Revision ID: 885f034e93c2
Revises: 533015c239d4
Create Date: 2026-07-08 22:09:03.957991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '885f034e93c2'
down_revision: Union[str, Sequence[str], None] = '533015c239d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        'service_orders',
        'order_number',
        type_=sa.Integer(),
        postgresql_using='order_number::integer',
        existing_type=sa.String(),
        existing_nullable=False,
    )

def downgrade():
    op.alter_column(
        'service_orders',
        'order_number',
        type_=sa.String(),
        postgresql_using='order_number::varchar',
        existing_type=sa.Integer(),
        existing_nullable=False,
    )

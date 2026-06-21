"""
Ponto central de importação dos models.

Alembic e o session.py devem importar daqui para garantir
que todos os models estejam registrados no metadata antes
de qualquer operação de migração ou criação de tabelas.

Uso em alembic/env.py:
    from app.models import Base  # noqa: F401
    target_metadata = Base.metadata
"""

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.company import Company, PlanTier
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.service_order import (
    ServiceOrder,
    ServiceItem,
    OrderStatus,
    OrderPriority,
    ItemType,
)
from app.models.subscription import Subscription, SubscriptionStatus

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    # Models
    "Company",
    "User",
    "Customer",
    "ServiceOrder",
    "ServiceItem",
    "Subscription",
    # Enums
    "PlanTier",
    "UserRole",
    "OrderStatus",
    "OrderPriority",
    "ItemType",
    "SubscriptionStatus",
]
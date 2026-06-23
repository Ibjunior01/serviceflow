"""
Schemas de Subscription — controle de plano SaaS por tenant.

Subscriptions são gerenciadas internamente (ou via webhook de pagamento).
O tenant comum não cria/edita subscriptions diretamente —
por isso os schemas são mais simples, focados em leitura e admin.
"""

from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import Field

from .common import BaseSchema
from app.models.company import PlanTier
from app.models.subscription import SubscriptionStatus


# ---------------------------------------------------------------------------
# Campos compartilhados
# ---------------------------------------------------------------------------

class SubscriptionBase(BaseSchema):
    plan_tier: PlanTier
    status: SubscriptionStatus
    price_paid: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=10,
        decimal_places=2,
        description="Valor pago neste ciclo (em BRL).",
    )
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Create — uso interno / admin (não exposto ao tenant comum)
# ---------------------------------------------------------------------------

class SubscriptionCreate(SubscriptionBase):
    company_id: UUID


# ---------------------------------------------------------------------------
# Update — PATCH /subscriptions/{id} (admin only)
# ---------------------------------------------------------------------------

class SubscriptionUpdate(BaseSchema):
    plan_tier: Optional[PlanTier] = None
    status: Optional[SubscriptionStatus] = None
    price_paid: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=10,
        decimal_places=2,
    )
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class SubscriptionResponse(SubscriptionBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    # Campos computados úteis para o frontend
    is_active: bool = Field(
        description="True se o plano está ativo ou em trial.",
    )
    days_remaining: Optional[int] = Field(
        default=None,
        description="Dias restantes no período atual (None se sem data de fim).",
    )
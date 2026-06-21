"""
Subscription — controle de plano SaaS por tenant.
Integração futura: Stripe ou Pagar.me.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company


class SubscriptionStatus(str, Enum):
    TRIALING = "trialing"   # período de trial
    ACTIVE = "active"       # assinatura ativa e paga
    PAST_DUE = "past_due"   # pagamento atrasado
    CANCELLED = "cancelled" # cancelada pelo usuário
    EXPIRED = "expired"     # expirou sem renovação


class Subscription(UUIDMixin, TimestampMixin, Base):
    """
    Controle de assinatura por Company.
    Uma Company tem no máximo uma Subscription ativa (1:1).
    """
    __tablename__ = "subscriptions"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    plan_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="free | basico | pro | empresa",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=SubscriptionStatus.TRIALING,
        nullable=False,
    )

    # Datas do ciclo de cobrança
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # IDs externos (gateway de pagamento)
    external_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="ID no Stripe / Pagar.me"
    )
    external_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Flags de controle de features
    is_annual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relacionamentos
    company: Mapped["Company"] = relationship(back_populates="subscription", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Subscription company_id={self.company_id} plan={self.plan_tier!r} status={self.status!r}>"
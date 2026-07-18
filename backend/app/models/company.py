"""
Company — raiz do tenant no modelo multi-tenant do ServiceFlow.
Um técnico autônomo é também uma Company (com apenas 1 usuário).
"""
import uuid
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.customer import Customer
    from app.models.service_order import ServiceOrder
    from app.models.subscription import Subscription


class PlanTier(str, Enum):
    FREE = "free"
    BASICO = "basico"
    PRO = "pro"
    EMPRESA = "empresa"


class Company(UUIDMixin, TimestampMixin, Base):
    """
    Tenant raiz. Pode representar:
    - Técnico autônomo (solo)
    - Empresa com múltiplos técnicos
    """
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    document: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="CNPJ ou CPF")
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, comment="UF ex: CE")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    plan_tier: Mapped[str] = mapped_column(
        String(20),
        default=PlanTier.FREE,
        nullable=False,
        comment="Plano ativo: free | basico | pro | empresa",
    )

    # Relacionamentos
    users: Mapped[List["User"]] = relationship(
        back_populates="company",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    customers: Mapped[List["Customer"]] = relationship(
        back_populates="company",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    service_orders: Mapped[List["ServiceOrder"]] = relationship(
        back_populates="company",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    subscription: Mapped[Optional["Subscription"]] = relationship(
        back_populates="company",
        uselist=False,
        lazy="selectin",
    )


    @property
    def subscription_status(self) -> Optional[str]:
        return self.subscription.status if self.subscription else None

    @property
    def trial_ends_at(self):
        return self.subscription.trial_ends_at if self.subscription else None
    

    def __repr__(self) -> str:
        return f"<Company id={self.id} slug={self.slug!r}>"
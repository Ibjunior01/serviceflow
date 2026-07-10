"""
ServiceOrder + ServiceItem — núcleo do domínio FSM do ServiceFlow.

Fluxo de status:
  DRAFT → SCHEDULED → IN_PROGRESS → COMPLETED → INVOICED
                                  ↘ CANCELLED
"""
import uuid
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.customer import Customer
    from app.models.user import User


class OrderStatus(str, Enum):
    DRAFT = "draft"             # rascunho, não agendada
    SCHEDULED = "scheduled"     # agendada com data/hora
    IN_PROGRESS = "in_progress" # técnico em campo
    COMPLETED = "completed"     # serviço executado
    INVOICED = "invoiced"       # fatura gerada/enviada
    CANCELLED = "cancelled"     # cancelada


class OrderPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ServiceOrder(UUIDMixin, TimestampMixin, Base):
    """
    Ordem de Serviço — entidade central do FSM.
    Contém o ciclo de vida completo do atendimento.
    """
    __tablename__ = "service_orders"

    # Tenant + Relacionamentos principais
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    technician_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Identificação
    order_number: Mapped[int] = mapped_column(
        Integer, 
        unique=True,
        nullable=False,
        index=True,
        comment="Ex: OS-2024-00042 (gerado no service layer)",
    )

    # Status e prioridade
    status: Mapped[str] = mapped_column(
        String(20),
        default=OrderStatus.DRAFT,
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(10),
        default=OrderPriority.NORMAL,
        nullable=False,
    )

    # Conteúdo
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Endereço do atendimento (pode diferir do Customer)
    service_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    service_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Agendamento
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Financeiro (totais calculados pelo service layer)
    labor_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    parts_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    discount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )

    # Assinatura do cliente (URL do arquivo)
    signature_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relacionamentos
    company: Mapped["Company"] = relationship(back_populates="service_orders", lazy="selectin")
    customer: Mapped["Customer"] = relationship(back_populates="service_orders", lazy="selectin")
    technician: Mapped[Optional["User"]] = relationship(
        back_populates="assigned_orders",
        foreign_keys=[technician_id],
        lazy="selectin",
    )
    items: Mapped[List["ServiceItem"]] = relationship(
        back_populates="service_order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ServiceOrder {self.order_number!r} status={self.status!r}>"


class ItemType(str, Enum):
    LABOR = "labor"       # mão de obra
    PART = "part"         # peça/material
    TRAVEL = "travel"     # deslocamento
    OTHER = "other"


class ServiceItem(UUIDMixin, TimestampMixin, Base):
    """
    Item de uma OS: peça, mão de obra, deslocamento, etc.
    """
    __tablename__ = "service_items"

    service_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("service_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(
        String(10),
        default=ItemType.PART,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), default=Decimal("1.000"), nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False,
        comment="quantity × unit_price (calculado no service layer)",
    )
    part_code: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Código do item no estoque"
    )

    # Relacionamentos
    service_order: Mapped["ServiceOrder"] = relationship(
        back_populates="items", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ServiceItem {self.description!r} qty={self.quantity}>"
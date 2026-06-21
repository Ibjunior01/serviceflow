"""
Customer — cliente atendido pela Company no ServiceFlow.
"""
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.service_order import ServiceOrder


class Customer(UUIDMixin, TimestampMixin, Base):
    """
    Pessoa física ou jurídica que solicita serviços.
    Pertence a um único tenant (Company).
    """
    __tablename__ = "customers"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    document: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="CPF ou CNPJ")
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Observações internas")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    company: Mapped["Company"] = relationship(back_populates="customers", lazy="selectin")
    service_orders: Mapped[List["ServiceOrder"]] = relationship(
        back_populates="customer",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} name={self.name!r}>"
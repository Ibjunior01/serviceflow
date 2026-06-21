"""
User — autenticação e controle de acesso (RBAC) do ServiceFlow.
"""
import uuid
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.service_order import ServiceOrder


class UserRole(str, Enum):
    OWNER = "owner"           # dono da empresa / técnico autônomo
    ADMIN = "admin"           # gestor sem acesso financeiro total
    TECHNICIAN = "technician" # executa OS, sem acesso admin
    VIEWER = "viewer"         # somente leitura (relatórios)


class User(UUIDMixin, TimestampMixin, Base):
    """
    Usuário do sistema. Sempre pertence a uma Company (tenant).
    O primeiro usuário de uma Company recebe role=OWNER automaticamente.
    """
    __tablename__ = "users"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20),
        default=UserRole.TECHNICIAN,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relacionamentos
    company: Mapped["Company"] = relationship(back_populates="users", lazy="selectin")
    assigned_orders: Mapped[List["ServiceOrder"]] = relationship(
        back_populates="technician",
        foreign_keys="ServiceOrder.technician_id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
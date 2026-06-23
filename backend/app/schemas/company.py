"""
Schemas de Company (tenant raiz do SaaS).

Company é criada no momento do cadastro — o owner se registra
junto com a empresa. Por isso CompanyCreate carrega também os
dados do primeiro usuário (owner).
"""

from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from .common import BaseSchema
from app.models.company import PlanTier


# ---------------------------------------------------------------------------
# Campos compartilhados
# ---------------------------------------------------------------------------

class CompanyBase(BaseSchema):
    name: str = Field(
        min_length=2,
        max_length=150,
        description="Nome da empresa ou autônomo.",
    )
    document: Optional[str] = Field(
        default=None,
        description="CPF (11 dígitos) ou CNPJ (14 dígitos) — apenas números.",
        examples=["12345678000199"],
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Telefone com DDD.",
        examples=["85999998888"],
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="E-mail principal da empresa.",
    )

    @field_validator("document")
    @classmethod
    def validate_document(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = "".join(filter(str.isdigit, v))
        if len(digits) not in (11, 14):
            raise ValueError("Documento deve ter 11 dígitos (CPF) ou 14 dígitos (CNPJ).")
        return digits


# ---------------------------------------------------------------------------
# Create — POST /companies (registro inicial do tenant)
# ---------------------------------------------------------------------------

class CompanyCreate(CompanyBase):
    """
    Payload de criação de empresa + owner.
    Usado no endpoint de registro público /auth/register.
    """

    # Dados do owner (primeiro usuário)
    owner_name: str = Field(min_length=2, max_length=150)
    owner_email: EmailStr
    owner_password: str = Field(min_length=8, max_length=128)

    @field_validator("owner_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("A senha deve conter pelo menos um número.")
        return v


# ---------------------------------------------------------------------------
# Update — PATCH /companies/{id}
# ---------------------------------------------------------------------------

class CompanyUpdate(BaseSchema):
    """Todos os campos são opcionais — PATCH parcial."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    document: Optional[str] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[EmailStr] = None


# ---------------------------------------------------------------------------
# Response — GET /companies/{id}
# ---------------------------------------------------------------------------

class CompanyResponse(CompanyBase):
    """
    Resposta completa da empresa.
    Inclui campos gerados pelo banco / sistema.
    """

    id: UUID
    plan_tier: PlanTier
    is_active: bool
    created_at: datetime
    updated_at: datetime
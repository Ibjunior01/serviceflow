"""
Schemas de Customer — clientes do tenant.

Clientes pertencem a um único tenant (company_id vem do JWT).
"""

from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from .common import BaseSchema


# ---------------------------------------------------------------------------
# Campos compartilhados
# ---------------------------------------------------------------------------

class CustomerBase(BaseSchema):
    name: str = Field(min_length=2, max_length=150)
    document: Optional[str] = Field(
        default=None,
        description="CPF (11) ou CNPJ (14) — apenas dígitos.",
    )
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)

    # Endereço (tudo opcional para clientes avulsos / sem cadastro completo)
    address_street: Optional[str] = Field(default=None, max_length=255)
    address_number: Optional[str] = Field(default=None, max_length=20)
    address_complement: Optional[str] = Field(default=None, max_length=100)
    address_neighborhood: Optional[str] = Field(default=None, max_length=100)
    address_city: Optional[str] = Field(default=None, max_length=100)
    address_state: Optional[str] = Field(default=None, max_length=2)
    address_zip: Optional[str] = Field(default=None, max_length=9)
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Observações internas sobre o cliente.",
    )

    @field_validator("document")
    @classmethod
    def validate_document(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        digits = "".join(filter(str.isdigit, v))
        if len(digits) not in (11, 14):
            raise ValueError("Documento deve ter 11 dígitos (CPF) ou 14 (CNPJ).")
        return digits

    @field_validator("address_state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return v.upper()


# ---------------------------------------------------------------------------
# Create — POST /customers
# ---------------------------------------------------------------------------

class CustomerCreate(CustomerBase):
    pass  # company_id vem do JWT no service layer


# ---------------------------------------------------------------------------
# Update — PATCH /customers/{id}
# ---------------------------------------------------------------------------

class CustomerUpdate(BaseSchema):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    document: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    address_street: Optional[str] = Field(default=None, max_length=255)
    address_number: Optional[str] = Field(default=None, max_length=20)
    address_complement: Optional[str] = Field(default=None, max_length=100)
    address_neighborhood: Optional[str] = Field(default=None, max_length=100)
    address_city: Optional[str] = Field(default=None, max_length=100)
    address_state: Optional[str] = Field(default=None, max_length=2)
    address_zip: Optional[str] = Field(default=None, max_length=9)
    notes: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# Response — GET /customers/{id}
# ---------------------------------------------------------------------------

class CustomerResponse(CustomerBase):
    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
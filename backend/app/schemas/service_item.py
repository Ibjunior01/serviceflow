"""
Schemas de ServiceItem — itens/peças dentro de uma OS.
"""

from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import Field, field_validator

from .common import BaseSchema
from app.models.service_order import ItemType


class ServiceItemBase(BaseSchema):
    item_type: ItemType = Field(description="Tipo do item: peça, mão de obra, etc.")
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(
        gt=Decimal("0"),
        max_digits=10,
        decimal_places=3,
        examples=[Decimal("1.5")],
    )
    unit_price: Decimal = Field(
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        examples=[Decimal("150.00")],
    )
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("quantity", "unit_price", mode="before")
    @classmethod
    def coerce_to_decimal(cls, v: object) -> Decimal:
        try:
            return Decimal(str(v))
        except Exception:
            raise ValueError(f"Valor inválido para campo decimal: {v!r}")


class ServiceItemCreate(ServiceItemBase):
    pass


class ServiceItemUpdate(BaseSchema):
    item_type: Optional[ItemType] = None
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(default=None, gt=Decimal("0"))
    unit_price: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    notes: Optional[str] = Field(default=None, max_length=500)


class ServiceItemResponse(ServiceItemBase):
    id: UUID
    service_order_id: UUID
    total_price: Decimal
    created_at: datetime
    updated_at: datetime
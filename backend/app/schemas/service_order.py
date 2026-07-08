"""
Schemas de ServiceOrder — núcleo do FSM.
"""

from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import Field

from .common import BaseSchema
from .service_item import ServiceItemCreate, ServiceItemResponse
from .user import UserPublic
from .customer import CustomerResponse
from app.models.service_order import OrderStatus, OrderPriority

from app.models.service_order import ServiceItem
from app.schemas.service_item import ServiceItemCreate


class ServiceOrderBase(BaseSchema):
    title: str = Field(
        min_length=3,
        max_length=255,
        examples=["Ar-condicionado Split não resfria — Apartamento 302"],
    )
    description: Optional[str] = Field(default=None, max_length=2000)
    priority: OrderPriority = Field(default=OrderPriority.NORMAL)
    scheduled_at: Optional[datetime] = None
    customer_id: UUID
    technician_id: Optional[UUID] = None
    location_address: Optional[str] = Field(default=None, max_length=500)
    location_reference: Optional[str] = Field(default=None, max_length=255)
    equipment_type: Optional[str] = Field(default=None, max_length=100)
    equipment_brand: Optional[str] = Field(default=None, max_length=100)
    equipment_model: Optional[str] = Field(default=None, max_length=100)
    equipment_serial: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)


class ServiceOrderCreate(ServiceOrderBase):
    items: list[ServiceItemCreate] = Field(default_factory=list)


class ServiceOrderUpdate(BaseSchema):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    priority: Optional[OrderPriority] = None
    scheduled_at: Optional[datetime] = None
    technician_id: Optional[UUID] = None
    location_address: Optional[str] = Field(default=None, max_length=500)
    location_reference: Optional[str] = Field(default=None, max_length=255)
    equipment_type: Optional[str] = Field(default=None, max_length=100)
    equipment_brand: Optional[str] = Field(default=None, max_length=100)
    equipment_model: Optional[str] = Field(default=None, max_length=100)
    equipment_serial: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)


class ServiceOrderStatusUpdate(BaseSchema):
    status: OrderStatus
    technician_notes: Optional[str] = Field(default=None, max_length=2000)


class ServiceOrderResponse(ServiceOrderBase):
    id: UUID
    order_number: str
    company_id: UUID
    status: OrderStatus
    total_amount: Decimal
    customer_name: Optional[str] = None
    technician_name: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ServiceOrderWithItems(ServiceOrderResponse):
    items: list[ServiceItemResponse] = Field(default_factory=list)
    customer: Optional[CustomerResponse] = None
    technician: Optional[UserPublic] = None


class ServiceOrderSummary(BaseSchema):
    id: UUID
    order_number: str
    title: str
    status: OrderStatus
    priority: OrderPriority
    customer_name: str
    technician_name: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    total_amount: Decimal
    created_at: datetime
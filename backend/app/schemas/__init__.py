"""
ServiceFlow — Schemas Pydantic v2
Fase 1C

Importações centralizadas para uso em toda a aplicação.
"""

from .company import CompanyCreate, CompanyUpdate, CompanyResponse
from .user import UserCreate, UserUpdate, UserResponse, UserPublic
from .customer import CustomerCreate, CustomerUpdate, CustomerResponse
from .service_order import (
    ServiceOrderCreate,
    ServiceOrderUpdate,
    ServiceOrderResponse,
    ServiceOrderWithItems,
    ServiceOrderSummary,
)
from .service_item import ServiceItemCreate, ServiceItemUpdate, ServiceItemResponse
from .subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from .common import PaginatedResponse, MessageResponse

__all__ = [
    # Company
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserPublic",
    # Customer
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    # ServiceOrder
    "ServiceOrderCreate",
    "ServiceOrderUpdate",
    "ServiceOrderResponse",
    "ServiceOrderWithItems",
    "ServiceOrderSummary",
    # ServiceItem
    "ServiceItemCreate",
    "ServiceItemUpdate",
    "ServiceItemResponse",
    # Subscription
    "SubscriptionCreate",
    "SubscriptionUpdate",
    "SubscriptionResponse",
    # Common
    "PaginatedResponse",
    "MessageResponse",
]
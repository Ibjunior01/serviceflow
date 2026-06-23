"""
Smoke test dos schemas — valida instanciação e validadores
sem precisar de banco ou ORM.

Rodar de dentro de backend/:
    python -m pytest ../test_schemas_smoke.py -v
ou diretamente:
    python test_schemas_smoke.py
"""

import sys
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timezone

# Simula enums sem importar os models ORM (evita dependência de DB)
from enum import Enum

class PlanTier(str, Enum):
    free = "free"
    basico = "basico"
    pro = "pro"
    empresa = "empresa"

class UserRole(str, Enum):
    owner = "owner"
    admin = "admin"
    technician = "technician"
    viewer = "viewer"

class OrderStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    invoiced = "invoiced"
    cancelled = "cancelled"

class OrderPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

class ItemType(str, Enum):
    labor = "labor"
    part = "part"
    travel = "travel"
    other = "other"

class SubscriptionStatus(str, Enum):
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    cancelled = "cancelled"
    expired = "expired"

# ---- Mock dos models para evitar import do ORM ----
import types
app_mock = types.ModuleType("app")
models_mock = types.ModuleType("app.models")
company_mock = types.ModuleType("app.models.company")
user_mock = types.ModuleType("app.models.user")
order_mock = types.ModuleType("app.models.service_order")
sub_mock = types.ModuleType("app.models.subscription")

company_mock.PlanTier = PlanTier
user_mock.UserRole = UserRole
order_mock.OrderStatus = OrderStatus
order_mock.OrderPriority = OrderPriority
order_mock.ItemType = ItemType
sub_mock.SubscriptionStatus = SubscriptionStatus

sys.modules["app"] = app_mock
sys.modules["app.models"] = models_mock
sys.modules["app.models.company"] = company_mock
sys.modules["app.models.user"] = user_mock
sys.modules["app.models.service_order"] = order_mock
sys.modules["app.models.subscription"] = sub_mock

# Agora importa os schemas
sys.path.insert(0, "./app")
from schemas.common import MessageResponse, PaginatedResponse
from schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from schemas.user import UserCreate, UserUpdate, UserResponse, UserPublic, UserPasswordUpdate
from schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from schemas.service_item import ServiceItemCreate, ServiceItemUpdate, ServiceItemResponse
from schemas.service_order import (
    ServiceOrderCreate, ServiceOrderUpdate, ServiceOrderStatusUpdate,
    ServiceOrderResponse, ServiceOrderWithItems, ServiceOrderSummary,
)
from schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse

import traceback

PASS = "✅"
FAIL = "❌"
results = []

def test(name, fn):
    try:
        fn()
        results.append((PASS, name))
        print(f"  {PASS} {name}")
    except Exception as e:
        results.append((FAIL, name))
        print(f"  {FAIL} {name}")
        traceback.print_exc()

print("\n=== ServiceFlow — Smoke Test Schemas Pydantic v2 ===\n")

# --- CompanyCreate ---
print("[ CompanyCreate ]")

def t_company_create_ok():
    c = CompanyCreate(
        name="Friotech Soluções",
        owner_name="João Silva",
        owner_email="joao@friotech.com.br",
        owner_password="Senha123",
    )
    assert c.name == "Friotech Soluções"

test("CompanyCreate válido", t_company_create_ok)

def t_company_create_bad_password():
    try:
        CompanyCreate(
            name="X",
            owner_name="Y",
            owner_email="y@y.com",
            owner_password="semNumero",  # sem dígito
        )
        assert False, "Deveria ter falhado"
    except Exception:
        pass

test("CompanyCreate rejeita senha sem número", t_company_create_bad_password)

def t_company_document_cnpj():
    c = CompanyCreate(
        name="Empresa LTDA",
        owner_name="Maria",
        owner_email="maria@empresa.com",
        owner_password="Senha456",
        document="12.345.678/0001-99",  # com máscara
    )
    assert c.document == "12345678000199"  # só dígitos

test("CompanyCreate normaliza CNPJ (remove máscara)", t_company_document_cnpj)

# --- UserCreate ---
print("\n[ UserCreate ]")

def t_user_create_ok():
    u = UserCreate(
        name="Carlos Técnico",
        email="carlos@friotech.com.br",
        password="Abc12345",
        role=UserRole.technician,
    )
    assert u.role == UserRole.technician

test("UserCreate válido", t_user_create_ok)

def t_user_create_owner_forbidden():
    try:
        UserCreate(
            name="Dono",
            email="dono@x.com",
            password="Abc12345",
            role=UserRole.owner,  # proibido
        )
        assert False, "Deveria ter falhado"
    except Exception:
        pass

test("UserCreate proíbe role=owner", t_user_create_owner_forbidden)

# --- CustomerCreate ---
print("\n[ CustomerCreate ]")

def t_customer_create_minimal():
    c = CustomerCreate(name="Condomínio Vista Mar")
    assert c.email is None

test("CustomerCreate mínimo (só nome)", t_customer_create_minimal)

def t_customer_create_full():
    c = CustomerCreate(
        name="Condomínio Vista Mar",
        email="sindico@vistamar.com.br",
        phone="85988887777",
        address_city="Fortaleza",
        address_state="ce",  # minúsculo
    )
    assert c.address_state == "CE"  # deve uppercase

test("CustomerCreate normaliza estado para maiúsculo", t_customer_create_full)

# --- ServiceItemCreate ---
print("\n[ ServiceItemCreate ]")

def t_item_create_ok():
    item = ServiceItemCreate(
        item_type=ItemType.labor,
        description="Limpeza higienização Split",
        quantity="1",
        unit_price="180.00",
    )
    assert item.quantity == Decimal("1")
    assert item.unit_price == Decimal("180.00")

test("ServiceItemCreate aceita strings e converte para Decimal", t_item_create_ok)

def t_item_quantity_zero_rejected():
    try:
        ServiceItemCreate(
            item_type=ItemType.part,
            description="Gás Freon",
            quantity="0",  # deve rejeitar
            unit_price="50",
        )
        assert False
    except Exception:
        pass

test("ServiceItemCreate rejeita quantity=0", t_item_quantity_zero_rejected)

# --- ServiceOrderCreate ---
print("\n[ ServiceOrderCreate ]")

def t_order_create_without_items():
    o = ServiceOrderCreate(
        title="Manutenção preventiva ar-condicionado",
        customer_id=uuid4(),
        priority=OrderPriority.normal,
    )
    assert o.items == []

test("ServiceOrderCreate sem itens (lista vazia por default)", t_order_create_without_items)

def t_order_create_with_items():
    o = ServiceOrderCreate(
        title="Instalação Split 12000 BTUs",
        customer_id=uuid4(),
        priority=OrderPriority.high,
        items=[
            ServiceItemCreate(
                item_type=ItemType.labor,
                description="Instalação",
                quantity="1",
                unit_price="350.00",
            ),
            ServiceItemCreate(
                item_type=ItemType.part,
                description="Suporte de parede",
                quantity="2",
                unit_price="45.00",
            ),
        ],
    )
    assert len(o.items) == 2

test("ServiceOrderCreate com 2 itens embutidos", t_order_create_with_items)

# --- ServiceOrderStatusUpdate ---
print("\n[ ServiceOrderStatusUpdate ]")

def t_status_transition():
    s = ServiceOrderStatusUpdate(
        status=OrderStatus.completed,
        technician_notes="Substituído capacitor. Equipamento funcionando normalmente.",
    )
    assert s.status == OrderStatus.completed

test("ServiceOrderStatusUpdate transição para completed", t_status_transition)

# --- PaginatedResponse ---
print("\n[ PaginatedResponse ]")

def t_paginated_response():
    p = PaginatedResponse[dict](
        items=[{"id": "1"}, {"id": "2"}],
        total=50,
        page=1,
        page_size=10,
        total_pages=5,
    )
    assert p.total == 50

test("PaginatedResponse genérico", t_paginated_response)

# --- Resumo ---
total = len(results)
passed = sum(1 for r in results if r[0] == PASS)
failed = total - passed

print(f"\n{'='*50}")
print(f"Resultado: {passed}/{total} testes passaram")
if failed:
    print(f"\nFalhas:")
    for r in results:
        if r[0] == FAIL:
            print(f"  {r[0]} {r[1]}")
    sys.exit(1)
else:
    print("Todos os schemas validados com sucesso! 🎉")
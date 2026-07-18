"""
ServiceFlow — Regras de limite por plano (feature gating).
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company, PlanTier
from app.models.customer import Customer
from app.models.service_order import ServiceOrder
from app.models.user import User, UserRole

# None = sem limite (ilimitado)
PLAN_LIMITS: dict[str, dict[str, int | None]] = {
    PlanTier.FREE: {"technicians": 1, "orders_per_month": 10, "customers": 5},
    PlanTier.BASICO: {"technicians": None, "orders_per_month": None, "customers": None},
    PlanTier.PRO: {"technicians": None, "orders_per_month": None, "customers": None},
    PlanTier.EMPRESA: {"technicians": None, "orders_per_month": None, "customers": None},
}


def _limit_for(plan_tier: str, key: str) -> int | None:
    return PLAN_LIMITS.get(plan_tier, {}).get(key)


# ── Contagens (reaproveitadas pelas checagens abaixo e pelo endpoint de uso) ──

async def count_customers(db: AsyncSession, company_id: UUID) -> int:
    stmt = select(func.count()).select_from(Customer).where(Customer.company_id == company_id)
    return (await db.execute(stmt)).scalar_one()


async def count_technicians(db: AsyncSession, company_id: UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(User)
        .where(User.company_id == company_id, User.role == UserRole.TECHNICIAN.value)
    )
    return (await db.execute(stmt)).scalar_one()


async def count_orders_this_month(db: AsyncSession, company_id: UUID) -> int:
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    stmt = (
        select(func.count())
        .select_from(ServiceOrder)
        .where(ServiceOrder.company_id == company_id, ServiceOrder.created_at >= start_of_month)
    )
    return (await db.execute(stmt)).scalar_one()


# ── Checagens (usadas nos endpoints de criação, lançam 403 se atingir o limite) ──

async def check_customer_limit(db: AsyncSession, company: Company) -> None:
    limit = _limit_for(company.plan_tier, "customers")
    if limit is None:
        return
    if await count_customers(db, company.id) >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limite do plano atingido: máximo de {limit} clientes cadastrados. Faça upgrade para adicionar mais.",
        )


async def check_technician_limit(db: AsyncSession, company: Company) -> None:
    limit = _limit_for(company.plan_tier, "technicians")
    if limit is None:
        return
    if await count_technicians(db, company.id) >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limite do plano atingido: máximo de {limit} técnico(s). Faça upgrade para adicionar mais.",
        )


async def check_order_limit(db: AsyncSession, company: Company) -> None:
    limit = _limit_for(company.plan_tier, "orders_per_month")
    if limit is None:
        return
    if await count_orders_this_month(db, company.id) >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limite do plano atingido: máximo de {limit} ordens de serviço por mês. Faça upgrade para criar mais.",
        )
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, OwnerOnly
from app.core.plan_limits import (
    PLAN_LIMITS,
    count_customers,
    count_orders_this_month,
    count_technicians,
)
from app.db.session import get_db
from app.schemas.company import CompanyResponse, CompanyUpdate, PlanUsageResponse
from app.services.company_service import company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=CompanyResponse)
async def get_my_company(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Retorna os dados da empresa do usuário autenticado."""
    return await company_service.get_or_404(db, current_user.company_id)


@router.patch("/me", response_model=CompanyResponse)
async def update_my_company(
    payload: CompanyUpdate,
    current_user: OwnerOnly,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza dados da empresa. Apenas OWNER."""
    return await company_service.update(db, company_id=current_user.company_id, data=payload)


@router.get("/me/usage", response_model=PlanUsageResponse)
async def get_my_usage(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Retorna uso atual vs. limites do plano da empresa."""
    company = current_user.company
    limits = PLAN_LIMITS.get(company.plan_tier, {})
    return PlanUsageResponse(
        plan_tier=company.plan_tier,
        technicians_used=await count_technicians(db, company.id),
        technicians_limit=limits.get("technicians"),
        orders_this_month_used=await count_orders_this_month(db, company.id),
        orders_this_month_limit=limits.get("orders_per_month"),
        customers_used=await count_customers(db, company.id),
        customers_limit=limits.get("customers"),
    )
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, OwnerOnly
from app.db.session import get_db
from app.schemas.company import CompanyResponse, CompanyUpdate
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

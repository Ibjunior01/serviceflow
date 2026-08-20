from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import TechOrAbove
from app.db.session import get_db
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import dashboard_service


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummary,
)
async def get_dashboard_summary(
    current_user: TechOrAbove,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna os indicadores operacionais do dashboard.

    OWNER e ADMIN:
        visualizam todas as ordens da empresa.

    TECHNICIAN:
        visualiza somente ordens atribuídas a ele.
    """
    return await dashboard_service.get_summary(
        db,
        company_id=current_user.company_id,
        requesting_user=current_user,
    )
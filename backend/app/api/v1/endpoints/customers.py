from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminOnly, TechOrAbove
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.services.customer_service import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    current_user: TechOrAbove,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Filtro por nome ou documento"),
):
    """Lista clientes da empresa. OWNER/ADMIN/TECHNICIAN."""
    return await customer_service.list(
        db,
        company_id=current_user.company_id,
        skip=(page - 1) * page_size,
        limit=page_size,
    )


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(
    payload: CustomerCreate,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo cliente. OWNER/ADMIN apenas."""
    return await customer_service.create(db, company_id=current_user.company_id, data=payload)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    current_user: TechOrAbove,
    db: AsyncSession = Depends(get_db),
):
    """Retorna um cliente pelo ID."""
    return await customer_service.get_or_404(db, customer_id, current_user.company_id)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza dados de um cliente. OWNER/ADMIN apenas."""
    return await customer_service.update(
        db, customer_id=customer_id, company_id=current_user.company_id, data=payload
    )


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: UUID,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    """Remove um cliente. OWNER/ADMIN apenas."""
    await customer_service.delete(db, customer_id=customer_id, company_id=current_user.company_id)
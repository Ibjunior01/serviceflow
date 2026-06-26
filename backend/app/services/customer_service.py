# app/services/customer_service.py
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.customer import customer_repo
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.common import PaginatedResponse
from app.core.exceptions import NotFoundError
from math import ceil


class CustomerService:
    async def get_or_404(
        self, db: AsyncSession, customer_id: UUID, company_id: UUID
    ) -> Customer:
        customer = await customer_repo.get_by_company_and_id(db, company_id, customer_id)
        if not customer:
            raise NotFoundError("Cliente não encontrado")
        return customer

    
    async def list(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> PaginatedResponse:
        items, total = await customer_repo.list_by_company(db, company_id, skip=skip, limit=limit)
        page = (skip // limit) + 1 if limit else 1
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=limit,
            total_pages=ceil(total / limit) if limit else 1,
        )

    async def update(
        self,
        db: AsyncSession,
        *,
        customer_id: UUID,
        company_id: UUID,
        data: CustomerUpdate,
    ) -> Customer:
        customer = await self.get_or_404(db, customer_id, company_id)
        return await customer_repo.update(
            db, db_obj=customer, obj_in=data.model_dump(exclude_unset=True)
        )
        
    
    async def create(
        self, db: AsyncSession, *, company_id: UUID, data: CustomerCreate
    ) -> Customer:
        return await customer_repo.create(
            db, obj_in={"company_id": company_id, **data.model_dump()}
        )
    

    async def delete(
        self, db: AsyncSession, *, customer_id: UUID, company_id: UUID
    ) -> None:
        customer = await self.get_or_404(db, customer_id, company_id)
        await customer_repo.delete(db, db_obj=customer)


customer_service = CustomerService()
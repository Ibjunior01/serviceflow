# app/repositories/customer.py
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.base import CRUDBase


class CustomerRepository(CRUDBase[Customer]):
    async def list_by_company(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Customer], int]:
        return await self.list(db, skip=skip, limit=limit, company_id=company_id)

    async def get_by_company_and_id(
        self, db: AsyncSession, company_id: UUID, customer_id: UUID
    ) -> Customer | None:
        result = await self.get_by(db, id=customer_id, company_id=company_id)
        return result


customer_repo = CustomerRepository(Customer)
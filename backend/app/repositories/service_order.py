# app/repositories/service_order.py
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.service_order import ServiceOrder, OrderStatus
from app.repositories.base import CRUDBase


class ServiceOrderRepository(CRUDBase[ServiceOrder]):

    async def get_with_items(
        self, db: AsyncSession, order_id: UUID, company_id: UUID
    ) -> ServiceOrder | None:
        stmt = (
            select(ServiceOrder)
            .options(selectinload(ServiceOrder.items))
            .where(
                ServiceOrder.id == order_id,
                ServiceOrder.company_id == company_id,
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_company(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        skip: int = 0,
        limit: int = 20,
        status: OrderStatus | None = None,
        technician_id: UUID | None = None,
        customer_id: UUID | None = None,
    ) -> tuple[list[ServiceOrder], int]:
        stmt = select(ServiceOrder).where(ServiceOrder.company_id == company_id)
        count_stmt = select(func.count()).select_from(ServiceOrder).where(
            ServiceOrder.company_id == company_id
        )

        if status is not None:
            stmt = stmt.where(ServiceOrder.status == status.value)
            count_stmt = count_stmt.where(ServiceOrder.status == status.value)
        if technician_id is not None:
            stmt = stmt.where(ServiceOrder.technician_id == technician_id)
            count_stmt = count_stmt.where(ServiceOrder.technician_id == technician_id)
        if customer_id is not None:
            stmt = stmt.where(ServiceOrder.customer_id == customer_id)
            count_stmt = count_stmt.where(ServiceOrder.customer_id == customer_id)

        total = (await db.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(ServiceOrder.created_at.desc()).offset(skip).limit(limit)
        items = list((await db.execute(stmt)).scalars().all())
        return items, total

    async def get_next_order_number(self, db: AsyncSession, company_id: UUID) -> int:
        stmt = select(func.count()).select_from(ServiceOrder).where(
            ServiceOrder.company_id == company_id
        )
        count = (await db.execute(stmt)).scalar_one()
        return count + 1


service_order_repo = ServiceOrderRepository(ServiceOrder)
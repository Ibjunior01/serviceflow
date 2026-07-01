# app/repositories/service_order.py
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.service_order import ServiceOrder, ServiceItem, OrderStatus
from app.repositories.base import CRUDBase
from app.schemas.service_item import ServiceItemCreate


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
        stmt = select(func.max(ServiceOrder.order_number)).where(
            ServiceOrder.company_id == company_id
        )
        max_number = (await db.execute(stmt)).scalar_one_or_none()
        return (int(max_number) if max_number else 0) + 1

    async def create_item(
        self,
        db: AsyncSession,
        *,
        order_id: UUID,
        data: ServiceItemCreate,
    ) -> ServiceItem:
        total = data.quantity * data.unit_price
        item = ServiceItem(
            service_order_id=order_id,
            description=data.description,
            item_type=data.item_type if isinstance(data.item_type, str) else data.item_type.value,
            quantity=data.quantity,
            unit_price=data.unit_price,
            total_price=total,
        )
        db.add(item)
        await db.flush()
        await db.refresh(item)
        return item

    async def get_item(
        self,
        db: AsyncSession,
        item_id: UUID,
        order_id: UUID,
    ) -> ServiceItem | None:
        result = await db.execute(
            select(ServiceItem).where(
                ServiceItem.id == item_id,
                ServiceItem.service_order_id == order_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_item(
        self, db: AsyncSession, *, item: ServiceItem
    ) -> None:
        await db.delete(item)
        await db.flush()


service_order_repo = ServiceOrderRepository(ServiceOrder)
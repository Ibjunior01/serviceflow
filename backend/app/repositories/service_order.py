from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.service_order import OrderStatus, ServiceItem, ServiceOrder
from app.repositories.base import CRUDBase
from app.schemas.service_item import ServiceItemCreate


class ServiceOrderRepository(CRUDBase[ServiceOrder]):

    async def get_with_items(
        self,
        db: AsyncSession,
        order_id: UUID,
        company_id: UUID,
    ) -> ServiceOrder | None:
        stmt = (
            select(ServiceOrder)
            .options(
                selectinload(ServiceOrder.items),
                selectinload(ServiceOrder.customer),
                selectinload(ServiceOrder.technician),
            )
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
        stmt = (
            select(ServiceOrder)
            .options(
                selectinload(ServiceOrder.customer),
                selectinload(ServiceOrder.technician),
            )
            .where(
                ServiceOrder.company_id == company_id,
            )
        )

        count_stmt = (
            select(func.count())
            .select_from(ServiceOrder)
            .where(
                ServiceOrder.company_id == company_id,
            )
        )

        if status is not None:
            stmt = stmt.where(
                ServiceOrder.status == status.value,
            )
            count_stmt = count_stmt.where(
                ServiceOrder.status == status.value,
            )

        if technician_id is not None:
            stmt = stmt.where(
                ServiceOrder.technician_id == technician_id,
            )
            count_stmt = count_stmt.where(
                ServiceOrder.technician_id == technician_id,
            )

        if customer_id is not None:
            stmt = stmt.where(
                ServiceOrder.customer_id == customer_id,
            )
            count_stmt = count_stmt.where(
                ServiceOrder.customer_id == customer_id,
            )

        total = (
            await db.execute(count_stmt)
        ).scalar_one()

        stmt = (
            stmt
            .order_by(ServiceOrder.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        items = list(
            (await db.execute(stmt))
            .scalars()
            .all()
        )

        return items, total

    async def count_by_status(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        technician_id: UUID | None = None,
    ) -> dict[str, int]:
        """
        Retorna a quantidade de ordens agrupada por status.

        Sempre respeita o tenant.
        Quando technician_id é informado, considera apenas
        ordens atribuídas ao técnico.
        """
        stmt = (
            select(
                ServiceOrder.status,
                func.count(ServiceOrder.id),
            )
            .where(
                ServiceOrder.company_id == company_id,
            )
            .group_by(
                ServiceOrder.status,
            )
        )

        if technician_id is not None:
            stmt = stmt.where(
                ServiceOrder.technician_id == technician_id,
            )

        result = await db.execute(stmt)

        return {
            status: int(count)
            for status, count in result.all()
        }

    async def count_by_month(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        start_date: datetime,
        technician_id: UUID | None = None,
    ) -> list[tuple[int, int, int]]:
        """
        Retorna quantidade de ordens agrupada por ano e mês.

        Formato:
            [(ano, mes, quantidade), ...]
        """
        year_expr = func.extract(
            "year",
            ServiceOrder.created_at,
        )

        month_expr = func.extract(
            "month",
            ServiceOrder.created_at,
        )

        stmt = (
            select(
                year_expr.label("year"),
                month_expr.label("month"),
                func.count(ServiceOrder.id).label("count"),
            )
            .where(
                ServiceOrder.company_id == company_id,
                ServiceOrder.created_at >= start_date,
            )
            .group_by(
                year_expr,
                month_expr,
            )
            .order_by(
                year_expr,
                month_expr,
            )
        )

        if technician_id is not None:
            stmt = stmt.where(
                ServiceOrder.technician_id == technician_id,
            )

        result = await db.execute(stmt)

        return [
            (
                int(year),
                int(month),
                int(count),
            )
            for year, month, count in result.all()
        ]

    async def list_recent(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        technician_id: UUID | None = None,
        limit: int = 8,
    ) -> list[ServiceOrder]:
        """
        Retorna as ordens mais recentes acessíveis.
        """
        stmt = (
            select(ServiceOrder)
            .options(
                selectinload(ServiceOrder.customer),
                selectinload(ServiceOrder.technician),
            )
            .where(
                ServiceOrder.company_id == company_id,
            )
        )

        if technician_id is not None:
            stmt = stmt.where(
                ServiceOrder.technician_id == technician_id,
            )

        stmt = (
            stmt
            .order_by(ServiceOrder.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(stmt)

        return list(
            result.scalars().all()
        )

    async def get_next_order_number(
        self,
        db: AsyncSession,
        company_id: UUID,
    ) -> int:
        stmt = (
            select(
                func.max(ServiceOrder.order_number)
            )
            .where(
                ServiceOrder.company_id == company_id,
            )
        )

        max_number = (
            await db.execute(stmt)
        ).scalar_one_or_none()

        return (
            int(max_number)
            if max_number
            else 0
        ) + 1

    async def create_item(
        self,
        db: AsyncSession,
        *,
        order_id: UUID,
        data: ServiceItemCreate,
    ) -> ServiceItem:
        total = (
            data.quantity
            * data.unit_price
        )

        item = ServiceItem(
            service_order_id=order_id,
            description=data.description,
            item_type=(
                data.item_type
                if isinstance(data.item_type, str)
                else data.item_type.value
            ),
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
        *,
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
        self,
        db: AsyncSession,
        *,
        item: ServiceItem,
    ) -> None:
        await db.delete(item)
        await db.flush()


service_order_repo = ServiceOrderRepository(
    ServiceOrder
)
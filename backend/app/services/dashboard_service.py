from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_order import OrderStatus
from app.models.user import User, UserRole
from app.repositories.service_order import service_order_repo
from app.schemas.dashboard import (
    DashboardMonthlyPoint,
    DashboardStatusCounts,
    DashboardSummary,
)
from app.schemas.service_order import ServiceOrderSummary


class DashboardService:

    def _get_effective_technician_id(
        self,
        requesting_user: User,
    ) -> UUID | None:
        """
        OWNER e ADMIN visualizam os dados de toda a empresa.

        TECHNICIAN visualiza somente ordens atribuídas
        ao próprio usuário.
        """
        if requesting_user.role == UserRole.TECHNICIAN.value:
            return requesting_user.id

        return None

    def _get_last_six_months(
        self,
        now: datetime,
    ) -> list[tuple[int, int]]:
        """
        Retorna os últimos seis meses, incluindo o mês atual.

        Exemplo:
            março até agosto de 2026.
        """
        months: list[tuple[int, int]] = []

        for offset in range(5, -1, -1):
            month_index = (
                now.year * 12
                + now.month
                - 1
                - offset
            )

            year = month_index // 12
            month = month_index % 12 + 1

            months.append(
                (year, month)
            )

        return months

    async def get_summary(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        requesting_user: User,
    ) -> DashboardSummary:
        """
        Retorna o resumo operacional do dashboard,
        respeitando tenant e RBAC.
        """
        technician_id = (
            self._get_effective_technician_id(
                requesting_user
            )
        )

        now = datetime.now(timezone.utc)

        months = self._get_last_six_months(
            now
        )

        first_year, first_month = months[0]

        start_date = datetime(
            first_year,
            first_month,
            1,
            tzinfo=timezone.utc,
        )

        status_counts_raw = (
            await service_order_repo.count_by_status(
                db,
                company_id,
                technician_id=technician_id,
            )
        )

        monthly_raw = (
            await service_order_repo.count_by_month(
                db,
                company_id,
                start_date=start_date,
                technician_id=technician_id,
            )
        )

        recent_orders_raw = (
            await service_order_repo.list_recent(
                db,
                company_id,
                technician_id=technician_id,
                limit=8,
            )
        )

        monthly_lookup = {
            (year, month): count
            for year, month, count in monthly_raw
        }

        monthly_orders = [
            DashboardMonthlyPoint(
                year=year,
                month=month,
                count=monthly_lookup.get(
                    (year, month),
                    0,
                ),
            )
            for year, month in months
        ]

        status_counts = DashboardStatusCounts(
            draft=status_counts_raw.get(
                OrderStatus.DRAFT.value,
                0,
            ),
            scheduled=status_counts_raw.get(
                OrderStatus.SCHEDULED.value,
                0,
            ),
            in_progress=status_counts_raw.get(
                OrderStatus.IN_PROGRESS.value,
                0,
            ),
            completed=status_counts_raw.get(
                OrderStatus.COMPLETED.value,
                0,
            ),
            invoiced=status_counts_raw.get(
                OrderStatus.INVOICED.value,
                0,
            ),
            cancelled=status_counts_raw.get(
                OrderStatus.CANCELLED.value,
                0,
            ),
        )

        recent_orders = [
            ServiceOrderSummary(
                id=order.id,
                order_number=order.order_number,
                title=order.title,
                status=order.status,
                priority=order.priority,
                customer_name=order.customer.name,
                technician_name=(
                    order.technician.full_name
                    if order.technician
                    else None
                ),
                total_amount=order.total_amount,
                created_at=order.created_at,
            )
            for order in recent_orders_raw
        ]

        return DashboardSummary(
            status_counts=status_counts,
            monthly_orders=monthly_orders,
            recent_orders=recent_orders,
        )


dashboard_service = DashboardService()
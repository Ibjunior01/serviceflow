# app/services/service_order_service.py
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_order import ServiceOrder, OrderStatus
from app.models.user import User, UserRole
from app.repositories.service_order import service_order_repo
from app.repositories.customer import customer_repo
from app.schemas.service_order import ServiceOrderCreate, ServiceOrderUpdate, ServiceOrderStatusUpdate
from app.core.exceptions import NotFoundError, ForbiddenError, BusinessRuleError

# Transições válidas de status
VALID_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.DRAFT: [OrderStatus.SCHEDULED, OrderStatus.CANCELLED],
    OrderStatus.SCHEDULED: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED],
    OrderStatus.IN_PROGRESS: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
    OrderStatus.COMPLETED: [OrderStatus.INVOICED],
    OrderStatus.INVOICED: [],
    OrderStatus.CANCELLED: [],
}


class ServiceOrderService:
    async def get_or_404(
        self, db: AsyncSession, order_id: UUID, company_id: UUID
    ) -> ServiceOrder:
        order = await service_order_repo.get_with_items(db, order_id, company_id)
        if not order:
            raise NotFoundError("Ordem de serviço não encontrada")
        return order

    async def list(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        skip: int = 0,
        limit: int = 20,
        status: OrderStatus | None = None,
        technician_id: UUID | None = None,
        customer_id: UUID | None = None,
    ):
        return await service_order_repo.list_by_company(
            db,
            company_id,
            skip=skip,
            limit=limit,
            status=status,
            technician_id=technician_id,
            customer_id=customer_id,
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        data: ServiceOrderCreate,
        created_by: User,
    ) -> ServiceOrder:
        # Valida cliente pertence ao tenant
        customer = await customer_repo.get_by_company_and_id(
            db, company_id, data.customer_id
        )
        if not customer:
            raise NotFoundError("Cliente não encontrado")

        order_number = await service_order_repo.get_next_order_number(db, company_id)

        order = await service_order_repo.create(
            db,
            obj_in={
                "company_id": company_id,
                "customer_id": data.customer_id,
                "technician_id": data.technician_id,
                "title": data.title,
                "description": data.description,
                "priority": data.priority.value if data.priority else OrderPriority.NORMAL.value,
                "status": OrderStatus.DRAFT.value,
                "scheduled_at": data.scheduled_at,
                "order_number": order_number,
                "created_by_id": created_by.id,
            },
        )
        return order

    async def update(
        self,
        db: AsyncSession,
        *,
        order_id: UUID,
        company_id: UUID,
        data: ServiceOrderUpdate,
        requesting_user: User,
    ) -> ServiceOrder:
        order = await self.get_or_404(db, order_id, company_id)

        if order.status in (OrderStatus.COMPLETED.value, OrderStatus.INVOICED.value, OrderStatus.CANCELLED.value):
            raise BusinessRuleError("Não é possível editar uma OS finalizada")

        # Técnico só edita OS atribuída a ele
        if requesting_user.role == UserRole.TECHNICIAN.value:
            if str(order.technician_id) != str(requesting_user.id):
                raise ForbiddenError("Técnico só pode editar suas próprias OS")

        return await service_order_repo.update(
            db, db_obj=order, obj_in=data.model_dump(exclude_unset=True)
        )

    async def change_status(
        self,
        db: AsyncSession,
        *,
        order_id: UUID,
        company_id: UUID,
        data: ServiceOrderStatusUpdate,
        requesting_user: User,
    ) -> ServiceOrder:
        order = await self.get_or_404(db, order_id, company_id)

        current = OrderStatus(order.status)
        new = data.status

        if new not in VALID_TRANSITIONS.get(current, []):
            raise BusinessRuleError(
                f"Transição inválida: {current.value} → {new.value}"
            )

        update_data: dict = {"status": new.value}

        # Timestamps automáticos
        now = datetime.now(timezone.utc)
        if new == OrderStatus.IN_PROGRESS:
            update_data["started_at"] = now
        elif new in (OrderStatus.COMPLETED, OrderStatus.CANCELLED):
            update_data["completed_at"] = now

        return await service_order_repo.update(db, db_obj=order, obj_in=update_data)

    async def delete(
        self, db: AsyncSession, *, order_id: UUID, company_id: UUID
    ) -> None:
        order = await self.get_or_404(db, order_id, company_id)
        if order.status != OrderStatus.DRAFT.value:
            raise BusinessRuleError("Apenas OS em rascunho pode ser excluída")
        await service_order_repo.delete(db, db_obj=order)


service_order_service = ServiceOrderService()
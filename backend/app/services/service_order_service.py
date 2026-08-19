# app/services/service_order_service.py
from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.models.service_order import OrderStatus, ServiceItem, ServiceOrder
from app.models.user import User, UserRole
from app.repositories.customer import customer_repo
from app.repositories.service_order import service_order_repo
from app.schemas.common import PaginatedResponse
from app.schemas.service_item import ServiceItemCreate
from app.schemas.service_order import (
    ServiceOrderCreate,
    ServiceOrderStatusUpdate,
    ServiceOrderSummary,
    ServiceOrderUpdate,
)


# Transições válidas de status
VALID_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.DRAFT: [
        OrderStatus.SCHEDULED,
        OrderStatus.CANCELLED,
    ],
    OrderStatus.SCHEDULED: [
        OrderStatus.IN_PROGRESS,
        OrderStatus.CANCELLED,
    ],
    OrderStatus.IN_PROGRESS: [
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    ],
    OrderStatus.COMPLETED: [
        OrderStatus.INVOICED,
    ],
    OrderStatus.INVOICED: [],
    OrderStatus.CANCELLED: [],
}


class ServiceOrderService:
    async def get_or_404(
        self,
        db: AsyncSession,
        order_id: UUID,
        company_id: UUID,
    ) -> ServiceOrder:
        """
        Busca uma OS garantindo o isolamento por empresa.
        """
        order = await service_order_repo.get_with_items(
            db,
            order_id,
            company_id,
        )

        if not order:
            raise NotFoundError(
                "Ordem de serviço não encontrada"
            )

        return order

    def _ensure_order_access(
        self,
        order: ServiceOrder,
        requesting_user: User,
    ) -> None:
        """
        OWNER e ADMIN podem acessar qualquer OS da própria empresa.

        TECHNICIAN pode acessar somente OS atribuídas a ele.
        """
        if requesting_user.role == UserRole.TECHNICIAN.value:
            if order.technician_id != requesting_user.id:
                raise ForbiddenError(
                    "Técnico só pode acessar ordens de serviço atribuídas a ele"
                )

    async def get_accessible_or_404(
        self,
        db: AsyncSession,
        order_id: UUID,
        company_id: UUID,
        requesting_user: User,
    ) -> ServiceOrder:
        """
        Busca uma OS garantindo:
        1. isolamento por empresa;
        2. escopo de acesso do técnico.
        """
        order = await self.get_or_404(
            db,
            order_id,
            company_id,
        )

        self._ensure_order_access(
            order,
            requesting_user,
        )

        return order

    async def list(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        requesting_user: User,
        skip: int,
        limit: int,
        status: OrderStatus | None,
        technician_id: UUID | None,
        customer_id: UUID | None,
    ) -> PaginatedResponse:
        """
        OWNER/ADMIN:
            podem visualizar todas as OS da empresa.

        TECHNICIAN:
            visualiza somente OS atribuídas a ele.
        """
        effective_technician_id = technician_id

        if requesting_user.role == UserRole.TECHNICIAN.value:
            effective_technician_id = requesting_user.id

        items, total = await service_order_repo.list_by_company(
            db,
            company_id,
            skip=skip,
            limit=limit,
            status=status,
            technician_id=effective_technician_id,
            customer_id=customer_id,
        )

        summaries = [
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
                scheduled_at=order.scheduled_at,
                total_amount=order.total_amount,
                created_at=order.created_at,
            )
            for order in items
        ]

        return PaginatedResponse(
            items=summaries,
            total=total,
            page=skip // limit + 1,
            page_size=limit,
            total_pages=(
                ceil(total / limit)
                if limit
                else 1
            ),
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        data: ServiceOrderCreate,
        created_by: User,
    ) -> ServiceOrder:
        customer = await customer_repo.get_by_company_and_id(
            db,
            company_id,
            data.customer_id,
        )

        if not customer:
            raise NotFoundError(
                "Cliente não encontrado"
            )

        order_number = (
            await service_order_repo.get_next_order_number(
                db,
                company_id,
            )
        )

        order = await service_order_repo.create(
            db,
            obj_in={
                "company_id": company_id,
                "customer_id": data.customer_id,
                "technician_id": data.technician_id,
                "title": data.title,
                "description": data.description,
                "priority": (
                    data.priority
                    if data.priority
                    else "normal"
                ),
                "status": OrderStatus.DRAFT.value,
                "scheduled_at": data.scheduled_at,
                "order_number": order_number,
                "service_address": data.location_address,
                "internal_notes": data.notes,
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
        order = await self.get_accessible_or_404(
            db,
            order_id,
            company_id,
            requesting_user,
        )

        if order.status in (
            OrderStatus.COMPLETED.value,
            OrderStatus.INVOICED.value,
            OrderStatus.CANCELLED.value,
        ):
            raise BusinessRuleError(
                "Não é possível editar uma OS finalizada"
            )

        # Técnico pode editar sua OS,
        # mas não pode reatribuir para outro técnico.
        if (
            requesting_user.role == UserRole.TECHNICIAN.value
            and "technician_id" in data.model_fields_set
        ):
            raise ForbiddenError(
                "Técnico não pode alterar a atribuição da ordem de serviço"
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        # Os nomes da API são diferentes dos nomes no model.
        if "location_address" in update_data:
            update_data["service_address"] = (
                update_data.pop("location_address")
            )

        if "notes" in update_data:
            update_data["internal_notes"] = (
                update_data.pop("notes")
            )

        return await service_order_repo.update(
            db,
            db_obj=order,
            obj_in=update_data,
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
        order = await self.get_accessible_or_404(
            db,
            order_id,
            company_id,
            requesting_user,
        )

        current = OrderStatus(order.status)

        new = (
            data.status
            if isinstance(data.status, str)
            else data.status.value
        )

        new_enum = OrderStatus(new)

        if new_enum not in VALID_TRANSITIONS.get(
            current,
            [],
        ):
            raise BusinessRuleError(
                f"Transição inválida: "
                f"{current.value} → {new}"
            )

        update_data: dict = {
            "status": new,
        }

        now = datetime.now(timezone.utc)

        if new == OrderStatus.IN_PROGRESS.value:
            update_data["started_at"] = now

        elif new in (
            OrderStatus.COMPLETED.value,
            OrderStatus.CANCELLED.value,
        ):
            update_data["completed_at"] = now

        return await service_order_repo.update(
            db,
            db_obj=order,
            obj_in=update_data,
        )

    async def delete(
        self,
        db: AsyncSession,
        *,
        order_id: UUID,
        company_id: UUID,
    ) -> None:
        # DELETE continua AdminOnly no endpoint.
        order = await self.get_or_404(
            db,
            order_id,
            company_id,
        )

        if order.status != OrderStatus.DRAFT.value:
            raise BusinessRuleError(
                "Apenas OS em rascunho pode ser excluída"
            )

        await service_order_repo.delete(
            db,
            db_obj=order,
        )

    async def add_item(
        self,
        db: AsyncSession,
        *,
        order_id: UUID,
        company_id: UUID,
        data: ServiceItemCreate,
        requesting_user: User,
    ) -> ServiceItem:
        order = await self.get_accessible_or_404(
            db,
            order_id,
            company_id,
            requesting_user,
        )

        if order.status in (
            OrderStatus.COMPLETED.value,
            OrderStatus.INVOICED.value,
            OrderStatus.CANCELLED.value,
        ):
            raise BusinessRuleError(
                "Não é possível adicionar itens a uma OS finalizada"
            )

        item = await service_order_repo.create_item(
            db,
            order_id=order_id,
            data=data,
        )

        new_total = (
            sum(
                existing_item.total_price
                for existing_item in order.items
            )
            + item.total_price
        )

        await service_order_repo.update(
            db,
            db_obj=order,
            obj_in={
                "total_amount": new_total,
            },
        )

        return item

    async def remove_item(
        self,
        db: AsyncSession,
        *,
        order_id: UUID,
        item_id: UUID,
        company_id: UUID,
        requesting_user: User,
    ) -> None:
        order = await self.get_accessible_or_404(
            db,
            order_id,
            company_id,
            requesting_user,
        )

        if order.status in (
            OrderStatus.COMPLETED.value,
            OrderStatus.INVOICED.value,
            OrderStatus.CANCELLED.value,
        ):
            raise BusinessRuleError(
                "Não é possível remover itens de uma OS finalizada"
            )

        item = await service_order_repo.get_item(
            db,
            item_id=item_id,
            order_id=order_id,
        )

        if not item:
            raise NotFoundError(
                "Item não encontrado nesta OS"
            )

        new_total = sum(
            existing_item.total_price
            for existing_item in order.items
            if existing_item.id != item_id
        )

        await service_order_repo.update(
            db,
            db_obj=order,
            obj_in={
                "total_amount": new_total,
            },
        )

        await service_order_repo.delete_item(
            db,
            item=item,
        )


service_order_service = ServiceOrderService()
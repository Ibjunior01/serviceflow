from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminOnly, TechOrAbove
from app.db.session import get_db
from app.models.service_order import OrderStatus
from app.schemas.common import PaginatedResponse
from app.schemas.service_item import ServiceItemCreate, ServiceItemResponse
from app.schemas.service_order import (
    ServiceOrderCreate,
    ServiceOrderResponse,
    ServiceOrderStatusUpdate,
    ServiceOrderSummary,
    ServiceOrderUpdate,
)
from app.services.service_order_service import service_order_service

router = APIRouter(prefix="/orders", tags=["service-orders"])


@router.get("", response_model=PaginatedResponse[ServiceOrderSummary])
async def list_orders(
    current_user: TechOrAbove,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = Query(None),
    technician_id: UUID | None = Query(None),
    customer_id: UUID | None = Query(None),
):
    return await service_order_service.list(
        db,
        company_id=current_user.company_id,
        skip=(page - 1) * page_size,
        limit=page_size,
        status=status,
        technician_id=technician_id,
        customer_id=customer_id,
    )


@router.post("", response_model=ServiceOrderResponse, status_code=201)
async def create_order(
    payload: ServiceOrderCreate,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    return await service_order_service.create(
        db, company_id=current_user.company_id, data=payload, created_by=current_user
    )


@router.get("/{order_id}", response_model=ServiceOrderResponse)
async def get_order(
    order_id: UUID,
    current_user: TechOrAbove,
    db: AsyncSession = Depends(get_db),
):
    order = await service_order_service.get_or_404(db, order_id, current_user.company_id)
    return ServiceOrderResponse(
        id=order.id,
        order_number=order.order_number,
        company_id=order.company_id,
        customer_id=order.customer_id,
        customer_name=order.customer.name if order.customer else None,
        technician_id=order.technician_id,
        technician_name=order.technician.full_name if order.technician else None,
        title=order.title,
        description=order.description,
        priority=order.priority,
        status=order.status,
        scheduled_at=order.scheduled_at,
        started_at=order.started_at,
        completed_at=order.completed_at,
        total_amount=order.total_amount,
        notes=order.internal_notes,
        location_address=order.service_address,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.patch("/{order_id}", response_model=ServiceOrderResponse)
async def update_order(
    order_id: UUID,
    payload: ServiceOrderUpdate,
    current_user: TechOrAbove,
    db: AsyncSession = Depends(get_db),
):
    return await service_order_service.update(
        db,
        order_id=order_id,
        company_id=current_user.company_id,
        data=payload,
        requesting_user=current_user,
    )


@router.delete("/{order_id}", status_code=204)
async def delete_order(
    order_id: UUID,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    await service_order_service.delete(db, order_id=order_id, company_id=current_user.company_id)


@router.patch("/{order_id}/status", response_model=ServiceOrderResponse)
async def update_order_status(
    order_id: UUID,
    payload: ServiceOrderStatusUpdate,
    current_user: TechOrAbove,
    db: AsyncSession = Depends(get_db),
):
    return await service_order_service.change_status(
        db,
        order_id=order_id,
        company_id=current_user.company_id,
        data=payload,
        requesting_user=current_user,
    )


@router.get("/{order_id}/items", response_model=list[ServiceItemResponse])
async def list_items(
    order_id: UUID,
    current_user: TechOrAbove,
    db: AsyncSession = Depends(get_db),
):
    order = await service_order_service.get_or_404(db, order_id, current_user.company_id)
    return order.items


@router.post("/{order_id}/items", response_model=ServiceItemResponse, status_code=201)
async def add_item(
    order_id: UUID,
    payload: ServiceItemCreate,
    current_user: TechOrAbove,
    db: AsyncSession = Depends(get_db),
):
    return await service_order_service.add_item(
        db,
        order_id=order_id,
        company_id=current_user.company_id,
        data=payload,
        requesting_user=current_user,
    )


@router.delete("/{order_id}/items/{item_id}", status_code=204)
async def remove_item(
    order_id: UUID,
    item_id: UUID,
    current_user: TechOrAbove,
    db: AsyncSession = Depends(get_db),
):
    await service_order_service.remove_item(
        db,
        order_id=order_id,
        item_id=item_id,
        company_id=current_user.company_id,
        requesting_user=current_user,
    )
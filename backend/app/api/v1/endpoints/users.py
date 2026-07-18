from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AdminOnly, CurrentUser, OwnerOnly
from app.db.session import get_db
from app.models.user import UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserRoleUpdate, UserUpdate
from app.services.user_service import user_service
from app.core.plan_limits import check_technician_limit

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return await user_service.list_by_company(
        db, company_id=current_user.company_id, page=page, page_size=page_size
    )


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    payload: UserCreate,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    role_value = payload.role.value if hasattr(payload.role, "value") else payload.role
    if role_value == UserRole.TECHNICIAN.value:
        await check_technician_limit(db, current_user.company)
    return await user_service.create(db, current_user.company_id, payload)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    return await user_service.get_or_404(db, user_id, current_user.company_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    is_self = current_user.id == user_id
    is_admin_or_above = current_user.role in (UserRole.OWNER.value, UserRole.ADMIN.value)

    if not is_self and not is_admin_or_above:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você só pode editar seu próprio perfil.")

    return await user_service.update(
        db, user_id, current_user.company_id, payload, requesting_user=current_user
    )


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    current_user: OwnerOnly,
    db: AsyncSession = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="O owner não pode remover a si mesmo.")
    await user_service.delete(db, user_id, current_user.company_id)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    payload: UserRoleUpdate,
    current_user: OwnerOnly,
    db: AsyncSession = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="O owner não pode alterar o próprio role.")
    return await user_service.update_role(db, user_id, current_user.company_id, payload)
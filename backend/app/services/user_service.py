# app/services/user_service.py
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user import user_repo
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserRoleUpdate, UserUpdate
from math import ceil
from app.schemas.common import PaginatedResponse


class UserService:

    async def get_or_404(
        self, db: AsyncSession, user_id: UUID, company_id: UUID
    ) -> User:
        user = await user_repo.get(db, user_id)
        if not user or user.company_id != company_id:
            raise NotFoundError("Usuário não encontrado")
        return user

    async def list_by_company(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        role: UserRole | None = None,
    ) -> PaginatedResponse[User]:
        skip = (page - 1) * page_size
        items, total = await user_repo.list_by_company(
            db, company_id, skip=skip, limit=page_size, role=role
        )
        # no list_by_company:
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if page_size else 1,
        )

    async def create(
        self,
        db: AsyncSession,
        company_id: UUID,
        data: UserCreate,
    ) -> User:
        if await user_repo.exists(db, email=data.email):
            raise ConflictError("E-mail já cadastrado")

        role = data.role.value if hasattr(data.role, "value") else data.role  # ← adicionar

        return await user_repo.create(
            db,
            obj_in={
                "company_id": company_id,
                "email": data.email,
                "full_name": data.full_name,
                "phone": data.phone,
                "hashed_password": hash_password(data.password),
                "role": role,  # ← usar aqui
                "is_active": True,
                "is_verified": False,
            },
            
        )

    async def update(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        data: UserUpdate,
        requesting_user: User | None = None,
    ) -> User:
        user = await self.get_or_404(db, user_id, company_id)
        update_data = data.model_dump(exclude_unset=True)

        # Role só pode ser alterado pelo OWNER — e não pode rebaixar o próprio owner
        if "role" in update_data:
            if requesting_user is None or requesting_user.role != UserRole.OWNER.value:
                raise ForbiddenError("Apenas o owner pode alterar roles")
            if user.role == UserRole.OWNER.value:
                raise ForbiddenError("Não é possível alterar o role do owner")

        if "password" in update_data:
            update_data["hashed_password"] = hash_password(update_data.pop("password"))

        return await user_repo.update(db, db_obj=user, obj_in=update_data)

    async def update_role(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        data: UserRoleUpdate,
    ) -> User:
        user = await self.get_or_404(db, user_id, company_id)

        if user.role == UserRole.OWNER.value:
            raise BusinessRuleError("Não é possível alterar o role do owner")

        return await user_repo.update(
            db, db_obj=user, obj_in={"role": data.role.value if hasattr(data.role, "value") else data.role}
        )

    async def delete(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
    ) -> None:
        user = await self.get_or_404(db, user_id, company_id)

        if user.role == UserRole.OWNER.value:
            raise BusinessRuleError("Não é possível remover o owner da empresa")

        await user_repo.delete(db, db_obj=user)


user_service = UserService()

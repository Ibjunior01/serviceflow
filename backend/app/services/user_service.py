# app/services/user_service.py
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.user import user_repo
from app.schemas.user import UserUpdate
from app.core.exceptions import NotFoundError, ConflictError, ForbiddenError
from app.core.security import get_password_hash


class UserService:
    async def get_or_404(
        self, db: AsyncSession, user_id: UUID, company_id: UUID
    ) -> User:
        user = await user_repo.get(db, user_id)
        if not user or user.company_id != company_id:
            raise NotFoundError("Usuário não encontrado")
        return user

    async def list(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        skip: int = 0,
        limit: int = 20,
        role: UserRole | None = None,
    ):
        return await user_repo.list_by_company(
            db, company_id, skip=skip, limit=limit, role=role
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        email: str,
        full_name: str,
        password: str,
        role: UserRole = UserRole.TECHNICIAN,
    ) -> User:
        if await user_repo.exists(db, email=email):
            raise ConflictError("E-mail já cadastrado")

        return await user_repo.create(
            db,
            obj_in={
                "company_id": company_id,
                "email": email,
                "full_name": full_name,
                "hashed_password": get_password_hash(password),
                "role": role.value,
                "is_active": True,
                "is_verified": False,
            },
        )

    async def update(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        company_id: UUID,
        data: UserUpdate,
        requesting_user: User,
    ) -> User:
        user = await self.get_or_404(db, user_id, company_id)

        update_data = data.model_dump(exclude_unset=True)

        # Somente OWNER pode mudar role
        if "role" in update_data:
            if requesting_user.role != UserRole.OWNER.value:
                raise ForbiddenError("Apenas o owner pode alterar roles")
            # Não pode rebaixar o próprio owner
            if user.role == UserRole.OWNER.value and str(user.id) != str(requesting_user.id):
                raise ForbiddenError("Não é possível alterar o role do owner")

        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        return await user_repo.update(db, db_obj=user, obj_in=update_data)

    async def deactivate(
        self, db: AsyncSession, *, user_id: UUID, company_id: UUID, requesting_user: User
    ) -> User:
        user = await self.get_or_404(db, user_id, company_id)

        if user.role == UserRole.OWNER.value:
            raise ForbiddenError("Não é possível desativar o owner")

        return await user_repo.update(db, db_obj=user, obj_in={"is_active": False})


user_service = UserService()
# app/repositories/user.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.base import CRUDBase


class UserRepository(CRUDBase[User]):
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        return await self.get_by(db, email=email)

    async def list_by_company(
        self,
        db: AsyncSession,
        company_id: UUID,
        *,
        skip: int = 0,
        limit: int = 20,
        role: UserRole | None = None,
    ) -> tuple[list[User], int]:
        filters: dict = {"company_id": company_id}
        if role is not None:
            filters["role"] = role.value
        return await self.list(db, skip=skip, limit=limit, **filters)


user_repo = UserRepository(User)
# app/repositories/company.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.repositories.base import CRUDBase


class CompanyRepository(CRUDBase[Company]):
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Company | None:
        return await self.get_by(db, slug=slug)

    async def get_by_document(self, db: AsyncSession, document: str) -> Company | None:
        return await self.get_by(db, document=document)


company_repo = CompanyRepository(Company)
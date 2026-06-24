# app/services/company_service.py
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.repositories.company import company_repo
from app.schemas.company import CompanyUpdate
from app.core.exceptions import NotFoundError, ConflictError


class CompanyService:
    async def get_or_404(self, db: AsyncSession, company_id: UUID) -> Company:
        company = await company_repo.get(db, company_id)
        if not company:
            raise NotFoundError("Empresa não encontrada")
        return company

    async def update(
        self, db: AsyncSession, *, company_id: UUID, data: CompanyUpdate
    ) -> Company:
        company = await self.get_or_404(db, company_id)

        update_data = data.model_dump(exclude_unset=True)

        if "document" in update_data and update_data["document"] != company.document:
            existing = await company_repo.get_by_document(db, update_data["document"])
            if existing:
                raise ConflictError("CNPJ/CPF já cadastrado")

        return await company_repo.update(db, db_obj=company, obj_in=update_data)


company_service = CompanyService()
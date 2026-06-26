"""
Schemas de User — autenticação + RBAC.
"""

from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator, model_validator

from .common import BaseSchema
from app.models.user import UserRole


class UserBase(BaseSchema):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    role: UserRole = Field(
        default=UserRole.TECHNICIAN,
        description="Papel do usuário no tenant.",
    )


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("A senha deve conter pelo menos um número.")
        if not any(c.isalpha() for c in v):
            raise ValueError("A senha deve conter pelo menos uma letra.")
        return v

    @model_validator(mode="after")
    def owner_role_forbidden(self) -> "UserCreate":
        if self.role == UserRole.OWNER:
            raise ValueError(
                "Não é possível criar um usuário com role 'owner' por esta rota. "
                "O owner é criado automaticamente no registro da empresa."
            )
        return self


class UserUpdate(BaseSchema):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=30)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class UserPasswordUpdate(BaseSchema):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("A nova senha deve conter pelo menos um número.")
        return v


class UserPublic(BaseSchema):
    id: UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    company_id: UUID
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    

class UserRoleUpdate(BaseSchema):
    role: UserRole
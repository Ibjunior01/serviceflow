"""
ServiceFlow — Endpoints de autenticação.

Rotas:
    POST /auth/register  — cadastro de empresa + owner
    POST /auth/login     — login com e-mail e senha
    POST /auth/refresh   — renovação de tokens
    GET  /auth/me        — dados do usuário autenticado
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.session import get_db
from app.schemas.company import CompanyCreate
from app.schemas.user import UserResponse
from app.services import auth_service

from app.core.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Auth"])

Session = Annotated[AsyncSession, Depends(get_db)]


# ---------------------------------------------------------------------------
# Schemas locais (simples demais para arquivo próprio)
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Usuário autenticado",
    description="Retorna os dados do usuário dono do access token.",
)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=201,
    summary="Cadastro de empresa + owner",
    description=(
        "Cria a empresa (tenant), o usuário owner e uma subscription de trial "
        "em uma única transação. Retorna tokens prontos para uso."
    ),
)
@limiter.limit("5/minute")
async def register(request: Request, payload: CompanyCreate, session: Session) -> Any:
    return await auth_service.register(payload, session)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login",
    description="Autentica com e-mail e senha. Retorna access + refresh token.",
)
@limiter.limit("10/minute")
async def login(request: Request, payload: LoginRequest, session: Session) -> Any:
    return await auth_service.login(payload.email, payload.password, session)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar tokens",
    description=(
        "Usa o refresh token para emitir um novo par de tokens (rotation). "
        "O refresh token anterior é descartado."
    ),
)
async def refresh(payload: RefreshRequest, session: Session) -> Any:
    return await auth_service.refresh_tokens(payload.refresh_token, session)
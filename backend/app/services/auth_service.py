"""
ServiceFlow — Auth Service.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone
from unicodedata import normalize
from uuid import UUID

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.company import Company, PlanTier
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User, UserRole
from app.schemas.company import CompanyCreate
from app.schemas.user import UserResponse


def _slugify(text: str) -> str:
    """Converte 'Friotech Soluções' → 'friotech-solucoes'"""
    text = normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text


class TokenPair:
    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = "bearer"

    def dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
        }


async def register(payload: CompanyCreate, session: AsyncSession) -> dict:
    # Verifica e-mail duplicado
    existing = await session.execute(
        select(User).where(User.email == payload.owner_email)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )

    # 1. Cria a empresa
    company = Company(
        name=payload.name,
        slug=f"{_slugify(payload.name)}-{str(uuid.uuid4())[:8]}",
        document=payload.document,
        phone=payload.phone,
        email=payload.email,
        plan_tier=PlanTier.FREE,
        is_active=True,
    )
    session.add(company)
    await session.flush()

    # 2. Cria o owner
    owner = User(
        company_id=company.id,
        full_name=payload.owner_name,
        email=payload.owner_email,
        hashed_password=hash_password(payload.owner_password),
        role=UserRole.OWNER,
        is_active=True,
        is_verified=False,
    )
    session.add(owner)
    await session.flush()

    # 3. Cria subscription de trial
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        company_id=company.id,
        plan_tier=PlanTier.FREE,
        status=SubscriptionStatus.TRIALING,
        trial_ends_at=now + timedelta(days=14),
        current_period_start=now,
        current_period_end=now + timedelta(days=14),
    )
    session.add(subscription)

    await session.commit()
    await session.refresh(owner)

    tokens = TokenPair(
        access_token=create_access_token(owner.id, company.id, owner.role),
        refresh_token=create_refresh_token(owner.id),
    )

    return {
        **tokens.dict(),
        "user": UserResponse.model_validate(owner).model_dump(),
    }


async def login(email: str, password: str, session: AsyncSession) -> dict:
    result = await session.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="E-mail ou senha inválidos.",
    )

    if user is None or not verify_password(password, user.hashed_password):
        raise invalid

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )

    tokens = TokenPair(
        access_token=create_access_token(user.id, user.company_id, user.role),
        refresh_token=create_refresh_token(user.id),
    )

    return {
        **tokens.dict(),
        "user": UserResponse.model_validate(user).model_dump(),
    }


async def refresh_tokens(refresh_token: str, session: AsyncSession) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token inválido ou expirado.",
    )

    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "refresh":
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await session.get(User, UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exception

    tokens = TokenPair(
        access_token=create_access_token(user.id, user.company_id, user.role),
        refresh_token=create_refresh_token(user.id),
    )

    return tokens.dict()
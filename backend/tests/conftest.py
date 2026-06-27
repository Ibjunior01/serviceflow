import os
from dotenv import load_dotenv

load_dotenv(".env.test", override=True)

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.session import get_db
from app.models import Base

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://serviceflow:serviceflow123@localhost:5432/serviceflow_test",
)


@pytest_asyncio.fixture()
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        async def override_get_db():
            yield session
        app.dependency_overrides[get_db] = override_get_db
        yield session
        app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture()
async def async_client(db_session):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


async def _register_and_login(client, payload):
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201, f"register falhou: {r.text}"
    login_r = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["owner_email"], "password": payload["owner_password"]},
    )
    assert login_r.status_code == 200, f"login falhou: {login_r.text}"
    return login_r.json()


async def _create_user_via_api(client, token, full_name, email, password, role):
    r = await client.post(
        "/api/v1/users",
        json={"full_name": full_name, "email": email, "password": password, "role": role},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, f"criacao de {role} falhou: {r.text}"
    return r.json()


async def _login(client, email, password):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, f"login falhou para {email}: {r.text}"
    return r.json()


@pytest_asyncio.fixture()
async def owner_tokens(async_client):
    return await _register_and_login(async_client, {
        "name": "Empresa Teste A",
        "owner_name": "Owner A",
        "owner_email": "owner@empresa-a.com",
        "owner_password": "Senha123",
    })


@pytest_asyncio.fixture()
async def owner_headers(owner_tokens):
    return {"Authorization": f"Bearer {owner_tokens['access_token']}"}


@pytest_asyncio.fixture()
async def admin_tokens(async_client, owner_tokens):
    await _create_user_via_api(
        async_client, owner_tokens["access_token"],
        "Admin A", "admin@empresa-a.com", "Senha123", "admin",
    )
    return await _login(async_client, "admin@empresa-a.com", "Senha123")


@pytest_asyncio.fixture()
async def admin_headers(admin_tokens):
    return {"Authorization": f"Bearer {admin_tokens['access_token']}"}


@pytest_asyncio.fixture()
async def tech_tokens(async_client, owner_tokens):
    await _create_user_via_api(
        async_client, owner_tokens["access_token"],
        "Tecnico A", "tech@empresa-a.com", "Senha123", "technician",
    )
    return await _login(async_client, "tech@empresa-a.com", "Senha123")


@pytest_asyncio.fixture()
async def tech_headers(tech_tokens):
    return {"Authorization": f"Bearer {tech_tokens['access_token']}"}


@pytest_asyncio.fixture()
async def tenant_b_tokens(async_client):
    return await _register_and_login(async_client, {
        "name": "Empresa Teste B",
        "owner_name": "Owner B",
        "owner_email": "owner@empresa-b.com",
        "owner_password": "Senha123",
    })


@pytest_asyncio.fixture()
async def tenant_b_headers(tenant_b_tokens):
    return {"Authorization": f"Bearer {tenant_b_tokens['access_token']}"}


@pytest_asyncio.fixture()
async def sample_customer(async_client, admin_headers):
    r = await async_client.post(
        "/api/v1/customers",
        json={
            "name": "Cliente Fixture",
            "email": "cliente@fixture.com",
            "phone": "85999990000",
            "address_street": "Rua Teste",
            "address_number": "100",
            "address_city": "Fortaleza",
            "address_state": "CE",
            "address_zip": "60000000",
        },
        headers=admin_headers,
    )
    assert r.status_code == 201, f"sample_customer falhou: {r.text}"
    return r.json()


@pytest_asyncio.fixture()
async def sample_order(async_client, admin_headers, sample_customer, tech_tokens):
    me_r = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tech_tokens['access_token']}"},
    )
    tech_id = me_r.json()["id"]
    r = await async_client.post(
        "/api/v1/orders",
        json={
            "title": "Manutencao Split 12.000 BTU",
            "description": "Limpeza e recarga de gas",
            "customer_id": sample_customer["id"],
            "assigned_to": tech_id,
            "priority": "high",
        },
        headers=admin_headers,
    )
    assert r.status_code == 201, f"sample_order falhou: {r.text}"
    return r.json()
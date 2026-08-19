from uuid import UUID
from app.models.company import Company

REGISTER_PAYLOAD = {
    "name": "Frigotech",
    "owner_name": "Jose Silva",
    "owner_email": "ceo@frigotech.com",
    "owner_password": "Senha123",
}


class TestRegister:
    async def test_register_success(self, async_client):
        r = await async_client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        assert r.status_code == 201
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_register_duplicate_email(self, async_client):
        payload = {
            "name": "Empresa Dup",
            "owner_name": "Dup User",
            "owner_email": "dup@empresa.com",
            "owner_password": "Senha123",
        }
        await async_client.post("/api/v1/auth/register", json=payload)
        r = await async_client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 409

    async def test_register_invalid_email(self, async_client):
        r = await async_client.post(
            "/api/v1/auth/register",
            json={"name": "X", "owner_name": "X", "owner_email": "nao-e-email", "owner_password": "Senha123"},
        )
        assert r.status_code == 422

    async def test_register_missing_fields(self, async_client):
        r = await async_client.post("/api/v1/auth/register", json={"name": "Incompleto"})
        assert r.status_code == 422


class TestLogin:
    async def test_login_success(self, async_client, owner_tokens):
        assert "access_token" in owner_tokens
        assert owner_tokens["token_type"] == "bearer"

    async def test_login_wrong_password(self, async_client, owner_tokens):
        r = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "owner@empresa-a.com", "password": "SenhaErrada"},
        )
        assert r.status_code == 401

    async def test_login_nonexistent_user(self, async_client):
        r = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "fantasma@none.com", "password": "Senha123"},
        )
        assert r.status_code == 401

    async def test_inactive_user_cannot_login(
        self,
        async_client,
        admin_headers,
        tech_tokens,
    ):
        me_r = await async_client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {tech_tokens['access_token']}"
            },
        )
        assert me_r.status_code == 200

        user_id = me_r.json()["id"]

        deactivate_r = await async_client.patch(
            f"/api/v1/users/{user_id}",
            json={
                "is_active": False,
            },
            headers=admin_headers,
        )

        assert deactivate_r.status_code == 200, deactivate_r.text
        assert deactivate_r.json()["is_active"] is False

        login_r = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "tech@empresa-a.com",
                "password": "Senha123",
            },
        )

        assert login_r.status_code == 403


class TestRefreshToken:
    async def test_refresh_success(self, async_client, owner_tokens):
        r = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": owner_tokens["refresh_token"]},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()

    async def test_refresh_invalid_token(self, async_client):
        r = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "token.invalido.aqui"},
        )
        assert r.status_code == 401


class TestMe:
    async def test_me_returns_current_user(self, async_client, owner_headers):
        r = await async_client.get("/api/v1/auth/me", headers=owner_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "owner@empresa-a.com"
        assert data["role"].upper() == "OWNER"

    async def test_me_unauthenticated(self, async_client):
        r = await async_client.get("/api/v1/auth/me")
        assert r.status_code == 401

    async def test_me_invalid_token(self, async_client):
        r = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer token.invalido"},
        )
        assert r.status_code == 401

    async def test_inactive_user_token_is_rejected(
        self,
        async_client,
        admin_headers,
        tech_tokens,
    ):
        headers = {
            "Authorization": f"Bearer {tech_tokens['access_token']}"
        }

        me_r = await async_client.get(
            "/api/v1/auth/me",
            headers=headers,
        )
        assert me_r.status_code == 200

        user_id = me_r.json()["id"]

        deactivate_r = await async_client.patch(
            f"/api/v1/users/{user_id}",
            json={
                "is_active": False,
            },
            headers=admin_headers,
        )

        assert deactivate_r.status_code == 200, deactivate_r.text

        blocked_r = await async_client.get(
            "/api/v1/auth/me",
            headers=headers,
        )

        assert blocked_r.status_code == 401

class TestJwtSecurity:
    async def test_access_token_cannot_be_used_as_refresh_token(
        self,
        async_client,
        owner_tokens,
    ):
        r = await async_client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": owner_tokens["access_token"],
            },
        )

        assert r.status_code == 401

    async def test_refresh_token_cannot_be_used_as_access_token(
        self,
        async_client,
        owner_tokens,
    ):
        r = await async_client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": (
                    f"Bearer {owner_tokens['refresh_token']}"
                )
            },
        )

        assert r.status_code == 401

    async def test_inactive_company_cannot_login(
        self,
        async_client,
        owner_tokens,
        db_session,
    ):
        company_id = UUID(
            owner_tokens["user"]["company_id"]
        )

        company = await db_session.get(
            Company,
            company_id,
        )

        assert company is not None

        company.is_active = False

        await db_session.commit()

        r = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "owner@empresa-a.com",
                "password": "Senha123",
            },
        )

        assert r.status_code == 403

    async def test_inactive_company_cannot_refresh_session(
        self,
        async_client,
        owner_tokens,
        db_session,
    ):
        company_id = UUID(
            owner_tokens["user"]["company_id"]
        )

        company = await db_session.get(
            Company,
            company_id,
        )

        assert company is not None

        company.is_active = False

        await db_session.commit()

        r = await async_client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": owner_tokens["refresh_token"],
            },
        )

        assert r.status_code == 403
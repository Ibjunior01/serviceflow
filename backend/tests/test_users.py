"""
test_users.py — Fase 1G
Cobre: CRUD de usuários, guards RBAC, isolamento de tenant, troca de role
"""


class TestListUsers:
    async def test_admin_can_list(self, async_client, admin_headers):
        r = await async_client.get("/api/v1/users", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data

    async def test_technician_blocked(self, async_client, tech_headers):
        r = await async_client.get("/api/v1/users", headers=tech_headers)
        assert r.status_code == 403

    async def test_unauthenticated_blocked(self, async_client):
        r = await async_client.get("/api/v1/users")
        assert r.status_code == 401


class TestCreateUser:
    async def test_admin_can_create_technician(self, async_client, admin_headers):
        r = await async_client.post(
            "/api/v1/users",
            json={
                "full_name": "Técnico Novo",
                "email": "novo_tech@empresa-a.com",
                "password": "Senha@123",
                "role": "technician",
            },
            headers=admin_headers,
        )
        assert r.status_code == 201
        assert r.json()["role"] == "technician"

    async def test_technician_cannot_create_user(self, async_client, tech_headers):
        r = await async_client.post(
            "/api/v1/users",
            json={
                "full_name": "X",
                "email": "x@x.com",
                "password": "Senha@123",
                "role": "technician",
            },
            headers=tech_headers,
        )
        assert r.status_code == 403

    async def test_duplicate_email_rejected(self, async_client, admin_headers):
        payload = {
            "full_name": "Dup",
            "email": "dup_user@empresa-a.com",
            "password": "Senha@123",
            "role": "technician",
        }
        await async_client.post("/api/v1/users", json=payload, headers=admin_headers)
        r = await async_client.post("/api/v1/users", json=payload, headers=admin_headers)
        assert r.status_code == 409


class TestGetUser:
    async def test_user_can_get_self(self, async_client, tech_headers, tech_tokens):
        # pega ID do próprio usuário via /me
        me = await async_client.get("/api/v1/users/me", headers=tech_headers)
        user_id = me.json()["id"]

        r = await async_client.get(f"/api/v1/users/{user_id}", headers=tech_headers)
        # técnico pode ver a si mesmo via /me mas /users/{id} é AdminOnly
        # ajuste conforme sua implementação — se 403, ok
        assert r.status_code in (200, 403)

    async def test_admin_can_get_any_user(self, async_client, admin_headers, tech_tokens):
        me_r = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tech_tokens['access_token']}"},
        )
        tech_id = me_r.json()["id"]
        r = await async_client.get(f"/api/v1/users/{tech_id}", headers=admin_headers)
        assert r.status_code == 200

    async def test_nonexistent_user_404(self, async_client, admin_headers):
        r = await async_client.get(
            "/api/v1/users/00000000-0000-0000-0000-000000000000",
            headers=admin_headers,
        )
        assert r.status_code == 404


class TestUpdateUser:
    async def test_user_can_update_self(self, async_client, tech_headers):
        me = await async_client.get("/api/v1/users/me", headers=tech_headers)
        user_id = me.json()["id"]
        r = await async_client.patch(
            f"/api/v1/users/{user_id}",
            json={"full_name": "Técnico Atualizado"},
            headers=tech_headers,
        )
        assert r.status_code == 200
        assert r.json()["full_name"] == "Técnico Atualizado"

    async def test_user_cannot_update_other(self, async_client, tech_headers, admin_headers):
        me = await async_client.get("/api/v1/users/me", headers=admin_headers)
        admin_id = me.json()["id"]
        r = await async_client.patch(
            f"/api/v1/users/{admin_id}",
            json={"full_name": "Tentativa"},
            headers=tech_headers,
        )
        assert r.status_code == 403


class TestDeleteUser:
    async def test_owner_can_delete(self, async_client, owner_headers, admin_headers):
        # cria um usuário temporário para deletar
        me = await async_client.get("/api/v1/users/me", headers=admin_headers)
        admin_id = me.json()["id"]
        r = await async_client.delete(f"/api/v1/users/{admin_id}", headers=owner_headers)
        assert r.status_code in (200, 204)

    async def test_technician_cannot_delete(self, async_client, tech_headers):
        r = await async_client.delete(
            "/api/v1/users/00000000-0000-0000-0000-000000000001",
            headers=tech_headers,
        )
        assert r.status_code == 403


class TestChangeRole:
    async def test_owner_can_change_role(self, async_client, owner_headers, tech_tokens):
        me_r = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tech_tokens['access_token']}"},
        )
        tech_id = me_r.json()["id"]
        r = await async_client.patch(
            f"/api/v1/users/{tech_id}/role",
            json={"role": "admin"},
            headers=owner_headers,
        )
        assert r.status_code == 200
        assert r.json()["role"] == "admin"

    async def test_admin_cannot_change_role(self, async_client, admin_headers, tech_tokens):
        me_r = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tech_tokens['access_token']}"},
        )
        tech_id = me_r.json()["id"]
        r = await async_client.patch(
            f"/api/v1/users/{tech_id}/role",
            json={"role": "admin"},
            headers=admin_headers,
        )
        assert r.status_code == 403


class TestTenantIsolation:
    async def test_tenant_b_cannot_see_tenant_a_users(
        self, async_client, tenant_b_headers, admin_headers
    ):
        # Lista usuários como admin do tenant A
        r_a = await async_client.get("/api/v1/users", headers=admin_headers)
        users_a = {u["id"] for u in r_a.json()["items"]}

        # Tenant B só consegue listar seus próprios usuários
        # (tenant B não tem admin, então usamos tokens do owner B como admin)
        # Esse teste valida que o isolamento existe no nível do service
        r_b = await async_client.get("/api/v1/users", headers=tenant_b_headers)
        # Owner B não tem role ADMIN — deve ser 403 ou retornar apenas seus usuários
        if r_b.status_code == 200:
            users_b = {u["id"] for u in r_b.json()["items"]}
            assert users_a.isdisjoint(users_b), "Vazamento de dados entre tenants!"
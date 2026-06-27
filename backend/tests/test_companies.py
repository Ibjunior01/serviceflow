"""
test_companies.py — Fase 1G
Cobre: GET /companies/me, PATCH /companies/me, guards de role
"""


class TestGetMyCompany:
    async def test_owner_can_get_company(self, async_client, owner_headers):
        r = await async_client.get("/api/v1/companies/me", headers=owner_headers)
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["name"] == "Empresa Teste A"

    async def test_technician_can_get_company(self, async_client, tech_headers):
        r = await async_client.get("/api/v1/companies/me", headers=tech_headers)
        assert r.status_code == 200

    async def test_unauthenticated_blocked(self, async_client):
        r = await async_client.get("/api/v1/companies/me")
        assert r.status_code == 401


class TestUpdateMyCompany:
    async def test_owner_can_update(self, async_client, owner_headers):
        r = await async_client.patch(
            "/api/v1/companies/me",
            json={"name": "Empresa Teste A Atualizada", "phone": "85999990001"},
            headers=owner_headers,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Empresa Teste A Atualizada"

    async def test_technician_cannot_update(self, async_client, tech_headers):
        r = await async_client.patch(
            "/api/v1/companies/me",
            json={"name": "Tentativa Técnico"},
            headers=tech_headers,
        )
        assert r.status_code == 403

    async def test_admin_cannot_update(self, async_client, admin_headers):
        r = await async_client.patch(
            "/api/v1/companies/me",
            json={"name": "Tentativa Admin"},
            headers=admin_headers,
        )
        assert r.status_code == 403
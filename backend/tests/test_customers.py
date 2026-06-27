"""
test_customers.py — Fase 1G
Cobre: CRUD de clientes, guards RBAC, isolamento de tenant
"""


class TestCreateCustomer:
    async def test_admin_can_create(self, async_client, admin_headers):
        r = await async_client.post(
            "/api/v1/customers",
            json={
                "name": "Mercado Frio Ltda",
                "email": "contato@mercadofrio.com",
                "phone": "85988880000",
                "address_street": "Av. Santos Dumont",
                "address_number": "1000",
                "address_city": "Fortaleza",
                "address_state": "CE",
                "address_zip": "60150160",
            },
            headers=admin_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Mercado Frio Ltda"
        assert "id" in data

    async def test_technician_cannot_create(self, async_client, tech_headers):
        r = await async_client.post(
            "/api/v1/customers",
            json={"name": "X", "email": "x@x.com", "phone": "85000000000"},
            headers=tech_headers,
        )
        assert r.status_code == 403

    async def test_unauthenticated_blocked(self, async_client):
        r = await async_client.post("/api/v1/customers", json={"name": "X"})
        assert r.status_code == 401


class TestListCustomers:
    async def test_technician_can_list(self, async_client, tech_headers, sample_customer):
        r = await async_client.get("/api/v1/customers", headers=tech_headers)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        ids = [c["id"] for c in data["items"]]
        assert sample_customer["id"] in ids

    async def test_pagination_params(self, async_client, admin_headers):
        r = await async_client.get(
            "/api/v1/customers?page=1&page_size=5",
            headers=admin_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "total_pages" in data


class TestGetCustomer:
    async def test_technician_can_get(self, async_client, tech_headers, sample_customer):
        r = await async_client.get(
            f"/api/v1/customers/{sample_customer['id']}",
            headers=tech_headers,
        )
        assert r.status_code == 200
        assert r.json()["id"] == sample_customer["id"]

    async def test_not_found(self, async_client, admin_headers):
        r = await async_client.get(
            "/api/v1/customers/00000000-0000-0000-0000-000000000000",
            headers=admin_headers,
        )
        assert r.status_code == 404


class TestUpdateCustomer:
    async def test_admin_can_update(self, async_client, admin_headers, sample_customer):
        r = await async_client.patch(
            f"/api/v1/customers/{sample_customer['id']}",
            json={"phone": "85911111111"},
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["phone"] == "85911111111"

    async def test_technician_cannot_update(self, async_client, tech_headers, sample_customer):
        r = await async_client.patch(
            f"/api/v1/customers/{sample_customer['id']}",
            json={"phone": "85922222222"},
            headers=tech_headers,
        )
        assert r.status_code == 403


class TestDeleteCustomer:
    async def test_admin_can_delete(self, async_client, admin_headers):
        # Cria e deleta um cliente temporário
        create_r = await async_client.post(
            "/api/v1/customers",
            json={
                "name": "Para Deletar",
                "email": "deletar@test.com",
                "phone": "85933330000",
            },
            headers=admin_headers,
        )
        customer_id = create_r.json()["id"]
        r = await async_client.delete(
            f"/api/v1/customers/{customer_id}",
            headers=admin_headers,
        )
        assert r.status_code in (200, 204)

    async def test_technician_cannot_delete(self, async_client, tech_headers, sample_customer):
        r = await async_client.delete(
            f"/api/v1/customers/{sample_customer['id']}",
            headers=tech_headers,
        )
        assert r.status_code == 403


class TestTenantIsolation:
    async def test_tenant_b_cannot_see_tenant_a_customers(
        self, async_client, sample_customer, tenant_b_headers
    ):
        """Tenant B não deve enxergar clientes do tenant A."""
        r = await async_client.get("/api/v1/customers", headers=tenant_b_headers)
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()["items"]]
        assert sample_customer["id"] not in ids, "Vazamento de cliente entre tenants!"

    async def test_tenant_b_cannot_get_tenant_a_customer(
        self, async_client, sample_customer, tenant_b_headers
    ):
        r = await async_client.get(
            f"/api/v1/customers/{sample_customer['id']}",
            headers=tenant_b_headers,
        )
        assert r.status_code in (403, 404), "Tenant B acessou cliente do Tenant A!"
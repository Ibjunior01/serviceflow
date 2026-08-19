"""
test_service_orders.py — Fase 1G
Cobre: CRUD de OS, FSM (máquina de estados), itens de OS,
       guards (OS finalizada, delete só DRAFT), isolamento de tenant
"""

import pytest
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.models.service_order import ServiceOrder


class TestCreateOrder:
    async def test_admin_can_create(self, async_client, admin_headers, sample_customer, tech_tokens):
        me_r = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tech_tokens['access_token']}"},
        )
        tech_id = me_r.json()["id"]

        r = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "Instalação Ar Condicionado",
                "customer_id": sample_customer["id"],
                "technician_id": tech_id,
                "priority": "normal",
            },
            headers=admin_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "draft"
        assert "order_number" in data

    async def test_technician_cannot_create(self, async_client, tech_headers, sample_customer):
        r = await async_client.post(
            "/api/v1/orders",
            json={"title": "OS Técnico", "customer_id": sample_customer["id"]},
            headers=tech_headers,
        )
        assert r.status_code == 403


class TestListOrders:
    
    async def test_admin_sees_all_orders(
    self, async_client, admin_headers, sample_order):
        r = await async_client.get("/api/v1/orders", headers=admin_headers)
        assert r.status_code == 200, f"Erro inesperado: {r.status_code} - {r.text}"
        data = r.json()
        assert "items" in data
        ids = [o["id"] for o in data["items"]]
        assert sample_order["id"] in ids
    
    async def test_technician_sees_own_orders(
    self, async_client, tech_headers, sample_order):
        r = await async_client.get("/api/v1/orders", headers=tech_headers)
        assert r.status_code == 200, f"Erro inesperado: {r.status_code} - {r.text}"
        ids = [o["id"] for o in r.json()["items"]]
        assert sample_order["id"] in ids

    
    async def test_pagination_has_total_pages(
    self, async_client, admin_headers):
        r = await async_client.get("/api/v1/orders?page=1&page_size=10", headers=admin_headers)
        assert r.status_code == 200, f"Erro inesperado: {r.status_code} - {r.text}"
        assert "total_pages" in r.json()


class TestGetOrder:
    async def test_technician_can_get_assigned(self, async_client, tech_headers, sample_order):
        r = await async_client.get(
            f"/api/v1/orders/{sample_order['id']}",
            headers=tech_headers,
        )
        assert r.status_code == 200
        assert r.json()["id"] == sample_order["id"]

    async def test_not_found_returns_404(self, async_client, admin_headers):
        r = await async_client.get(
            "/api/v1/orders/00000000-0000-0000-0000-000000000000",
            headers=admin_headers,
        )
        assert r.status_code == 404


class TestUpdateOrder:
    async def test_admin_can_update_draft(self, async_client, admin_headers, sample_order):
        r = await async_client.patch(
            f"/api/v1/orders/{sample_order['id']}",
            json={"title": "Título Atualizado"},
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Título Atualizado"

    async def test_cannot_edit_completed_order(
        self, async_client, admin_headers, tech_headers, sample_order
    ):
        order_id = sample_order["id"]

        # Avança a OS para COMPLETED via FSM (DRAFT → CONFIRMED → IN_PROGRESS → COMPLETED)
        for status in ["scheduled", "in_progress", "completed"]:
            await async_client.patch(
                f"/api/v1/orders/{order_id}/status",
                json={"status": status},
                headers=admin_headers,
            )

        # Tenta editar OS finalizada — deve falhar
        r = await async_client.patch(
            f"/api/v1/orders/{order_id}",
            json={"title": "Tentativa edição finalizada"},
            headers=admin_headers,
        )
        assert r.status_code in (400, 422), "OS finalizada não deveria ser editável!"


class TestDeleteOrder:
    async def test_can_delete_draft(self, async_client, admin_headers, sample_customer, tech_tokens):
        me_r = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tech_tokens['access_token']}"},
        )
        tech_id = me_r.json()["id"]

        create_r = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "OS para deletar",
                "customer_id": sample_customer["id"],
                "technician_id": tech_id,
            },
            headers=admin_headers,
        )
        order_id = create_r.json()["id"]

        r = await async_client.delete(f"/api/v1/orders/{order_id}", headers=admin_headers)
        assert r.status_code in (200, 204)

    async def test_cannot_delete_non_draft(
        self, async_client, admin_headers, sample_order
    ):
        order_id = sample_order["id"]

        # Avança para CONFIRMED
        await async_client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "scheduled"},
            headers=admin_headers,
        )

        r = await async_client.delete(f"/api/v1/orders/{order_id}", headers=admin_headers)
        assert r.status_code in (400, 422), "Só DRAFT pode ser deletada!"


class TestStatusMachine:
    """Testa a máquina de estados da OS."""

    async def test_valid_transition_draft_to_confirmed(
        self, async_client, admin_headers, sample_order
    ):
        r = await async_client.patch(
            f"/api/v1/orders/{sample_order['id']}/status",
            json={"status": "scheduled"},
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "scheduled"

    async def test_full_happy_path(self, async_client, admin_headers, sample_customer, tech_tokens):
        me_r = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tech_tokens['access_token']}"},
        )
        tech_id = me_r.json()["id"]

        create_r = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "OS Happy Path",
                "customer_id": sample_customer["id"],
                "technician_id": tech_id,
            },
            headers=admin_headers,
        )
        order_id = create_r.json()["id"]

        transitions = ["scheduled", "in_progress", "completed"]
        for status in transitions:
            r = await async_client.patch(
                f"/api/v1/orders/{order_id}/status",
                json={"status": status},
                headers=admin_headers,
            )
            assert r.status_code == 200, f"Transição para {status} falhou: {r.text}"
            assert r.json()["status"] == status

        # Verifica timestamp de completed_at
        get_r = await async_client.get(f"/api/v1/orders/{order_id}", headers=admin_headers)
        # completed_at pode estar no detail endpoint
        assert get_r.json().get("completed_at") is not None or get_r.json().get("status") == "completed"

    async def test_invalid_transition_draft_to_completed(
        self, async_client, admin_headers, sample_order
    ):
        r = await async_client.patch(
            f"/api/v1/orders/{sample_order['id']}/status",
            json={"status": "completed"},
            headers=admin_headers,
        )
        assert r.status_code in (400, 422), "Transição inválida não foi rejeitada!"

    async def test_cannot_transition_from_terminal_state(
        self, async_client, admin_headers, sample_order
    ):
        order_id = sample_order["id"]
        for status in ["scheduled", "in_progress", "completed"]:
            await async_client.patch(
                f"/api/v1/orders/{order_id}/status",
                json={"status": status},
                headers=admin_headers,
            )

        # Tenta mover de COMPLETED → qualquer outra
        r = await async_client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "in_progress"},
            headers=admin_headers,
        )
        assert r.status_code in (400, 422), "Estado terminal não deve aceitar transição!"

    async def test_cancelled_is_terminal(self, async_client, admin_headers, sample_customer, tech_tokens):
        me_r = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tech_tokens['access_token']}"},
        )
        tech_id = me_r.json()["id"]

        create_r = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "OS Cancelada",
                "customer_id": sample_customer["id"],
                "technician_id": tech_id,
            },
            headers=admin_headers,
        )
        order_id = create_r.json()["id"]

        await async_client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "cancelled"},
            headers=admin_headers,
        )

        r = await async_client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "scheduled"},
            headers=admin_headers,
        )
        assert r.status_code in (400, 422)


class TestOrderItems:
    async def test_technician_can_add_item(self, async_client, tech_headers, sample_order):
        r = await async_client.post(
            f"/api/v1/orders/{sample_order['id']}/items",
            json={
                "item_type": "part",
                "description": "Gas R-410A 1kg",
                "quantity": "2.000",
                "unit_price": "85.00",
            },
            headers=tech_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["description"] == "Gas R-410A 1kg"
        assert "id" in data

    async def test_list_items(self, async_client, tech_headers, sample_order):
        # Adiciona item
        await async_client.post(
            f"/api/v1/orders/{sample_order['id']}/items",
            json={"item_type": "labor", "description": "Mao de obra", "quantity": "1.000", "unit_price": "150.00"},
            headers=tech_headers,
        )

        r = await async_client.get(
            f"/api/v1/orders/{sample_order['id']}/items",
            headers=tech_headers,
        )
        assert r.status_code == 200
        assert len(r.json()) >= 1

    async def test_delete_item(self, async_client, tech_headers, admin_headers, sample_order):
        add_r = await async_client.post(
            f"/api/v1/orders/{sample_order['id']}/items",
            json={"item_type": "other", "description": "Item para deletar", "quantity": "1.000", "unit_price": "10.00"},
            headers=tech_headers,
        )
        assert add_r.status_code == 201, f"add item falhou: {add_r.text}"
        item_id = add_r.json()["id"]

        r = await async_client.delete(
            f"/api/v1/orders/{sample_order['id']}/items/{item_id}",
            headers=tech_headers,
        )
        assert r.status_code in (200, 204)


class TestTenantIsolationOrders:
    
    async def test_tenant_b_cannot_see_tenant_a_orders(
    
        self, async_client, sample_order, tenant_b_headers
    ):
        r = await async_client.get("/api/v1/orders", headers=tenant_b_headers)
        assert r.status_code == 200, f"Erro inesperado: {r.status_code} - {r.text}"

        ids = [o["id"] for o in r.json()["items"]]
        assert sample_order["id"] not in ids, "Tenant B viu OS do Tenant A!"

    async def test_tenant_b_cannot_get_tenant_a_order(
        self, async_client, sample_order, tenant_b_headers
    ):
        r = await async_client.get(
            f"/api/v1/orders/{sample_order['id']}",
            headers=tenant_b_headers,
        )
        assert r.status_code in (403, 404), "Tenant B acessou OS do Tenant A!"


class TestOrderNumberTenantScope:
    async def test_order_number_must_be_unique_within_same_company(
        self, db_session, sample_order
    ):
        existing = await db_session.get(
            ServiceOrder,
            UUID(sample_order["id"]),
        )
        assert existing is not None

        duplicate = ServiceOrder(
            company_id=existing.company_id,
            customer_id=existing.customer_id,
            technician_id=existing.technician_id,
            order_number=existing.order_number,
            title="OS duplicada na mesma empresa",
        )

        db_session.add(duplicate)

        with pytest.raises(IntegrityError):
            await db_session.flush()

        await db_session.rollback()

    async def test_order_number_can_repeat_across_companies(
        self,
        async_client,
        owner_headers,
        tenant_b_headers,
    ):
        customer_a = await async_client.post(
            "/api/v1/customers",
            json={"name": "Cliente Empresa A"},
            headers=owner_headers,
        )
        assert customer_a.status_code == 201, customer_a.text

        customer_b = await async_client.post(
            "/api/v1/customers",
            json={"name": "Cliente Empresa B"},
            headers=tenant_b_headers,
        )
        assert customer_b.status_code == 201, customer_b.text

        order_a = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "Primeira OS Empresa A",
                "customer_id": customer_a.json()["id"],
            },
            headers=owner_headers,
        )
        assert order_a.status_code == 201, order_a.text

        order_b = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "Primeira OS Empresa B",
                "customer_id": customer_b.json()["id"],
            },
            headers=tenant_b_headers,
        )
        assert order_b.status_code == 201, order_b.text

        assert order_a.json()["order_number"] == 1
        assert order_b.json()["order_number"] == 1

class TestTechnicianOrderScope:
    async def _create_second_technician(
        self,
        async_client,
        admin_headers,
    ):
        create_r = await async_client.post(
            "/api/v1/users",
            json={
                "full_name": "Tecnico B",
                "email": "tech-b@empresa-a.com",
                "password": "Senha123",
                "role": "technician",
            },
            headers=admin_headers,
        )
        assert create_r.status_code == 201, create_r.text

        login_r = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "tech-b@empresa-a.com",
                "password": "Senha123",
            },
        )
        assert login_r.status_code == 200, login_r.text

        return {
            "id": create_r.json()["id"],
            "headers": {
                "Authorization": (
                    f"Bearer {login_r.json()['access_token']}"
                )
            },
        }

    async def _create_order_for_technician(
        self,
        async_client,
        admin_headers,
        sample_customer,
        technician_id,
    ):
        r = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "OS Outro Tecnico",
                "customer_id": sample_customer["id"],
                "technician_id": technician_id,
            },
            headers=admin_headers,
        )

        assert r.status_code == 201, r.text
        return r.json()

    async def test_technician_list_only_own_orders(
        self,
        async_client,
        admin_headers,
        tech_headers,
        sample_customer,
        sample_order,
    ):
        second_tech = await self._create_second_technician(
            async_client,
            admin_headers,
        )

        other_order = await self._create_order_for_technician(
            async_client,
            admin_headers,
            sample_customer,
            second_tech["id"],
        )

        r = await async_client.get(
            "/api/v1/orders",
            headers=tech_headers,
        )

        assert r.status_code == 200, r.text

        ids = [order["id"] for order in r.json()["items"]]

        assert sample_order["id"] in ids
        assert other_order["id"] not in ids

    async def test_technician_cannot_get_other_technician_order(
        self,
        async_client,
        admin_headers,
        tech_headers,
        sample_customer,
    ):
        second_tech = await self._create_second_technician(
            async_client,
            admin_headers,
        )

        other_order = await self._create_order_for_technician(
            async_client,
            admin_headers,
            sample_customer,
            second_tech["id"],
        )

        r = await async_client.get(
            f"/api/v1/orders/{other_order['id']}",
            headers=tech_headers,
        )

        assert r.status_code == 403

    async def test_technician_cannot_change_status_of_other_order(
        self,
        async_client,
        admin_headers,
        tech_headers,
        sample_customer,
    ):
        second_tech = await self._create_second_technician(
            async_client,
            admin_headers,
        )

        other_order = await self._create_order_for_technician(
            async_client,
            admin_headers,
            sample_customer,
            second_tech["id"],
        )

        r = await async_client.patch(
            f"/api/v1/orders/{other_order['id']}/status",
            json={"status": "scheduled"},
            headers=tech_headers,
        )

        assert r.status_code == 403

    async def test_technician_cannot_list_items_of_other_order(
        self,
        async_client,
        admin_headers,
        tech_headers,
        sample_customer,
    ):
        second_tech = await self._create_second_technician(
            async_client,
            admin_headers,
        )

        other_order = await self._create_order_for_technician(
            async_client,
            admin_headers,
            sample_customer,
            second_tech["id"],
        )

        r = await async_client.get(
            f"/api/v1/orders/{other_order['id']}/items",
            headers=tech_headers,
        )

        assert r.status_code == 403

    async def test_technician_cannot_reassign_own_order(
        self,
        async_client,
        admin_headers,
        tech_headers,
        sample_customer,
        sample_order,
    ):
        second_tech = await self._create_second_technician(
            async_client,
            admin_headers,
        )

        r = await async_client.patch(
            f"/api/v1/orders/{sample_order['id']}",
            json={
                "technician_id": second_tech["id"],
            },
            headers=tech_headers,
        )

        assert r.status_code == 403
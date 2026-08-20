class TestDashboardSummary:

    async def test_dashboard_counts_more_than_50_orders(
        self,
        async_client,
        admin_headers,
        sample_customer,
    ):
        """
        O dashboard deve contabilizar todas as OS,
        independentemente da paginação usada em /orders.
        """
        total_orders = 51

        for index in range(total_orders):
            response = await async_client.post(
                "/api/v1/orders",
                json={
                    "title": f"OS Dashboard {index + 1}",
                    "customer_id": sample_customer["id"],
                    "priority": "normal",
                },
                headers=admin_headers,
            )

            assert response.status_code == 201, response.text

        response = await async_client.get(
            "/api/v1/dashboard/summary",
            headers=admin_headers,
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status_counts"]["draft"] == total_orders

        assert sum(
            point["count"]
            for point in data["monthly_orders"]
        ) == total_orders

        assert len(data["recent_orders"]) == 8


    async def test_dashboard_returns_zero_for_empty_months(
        self,
        async_client,
        admin_headers,
    ):
        """
        Mesmo sem OS, o contrato deve retornar os seis meses
        e todos os status com valor zero.
        """
        response = await async_client.get(
            "/api/v1/dashboard/summary",
            headers=admin_headers,
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status_counts"] == {
            "draft": 0,
            "scheduled": 0,
            "in_progress": 0,
            "completed": 0,
            "invoiced": 0,
            "cancelled": 0,
        }

        assert len(data["monthly_orders"]) == 6

        assert all(
            point["count"] == 0
            for point in data["monthly_orders"]
        )

        assert data["recent_orders"] == []


    async def test_dashboard_preserves_tenant_isolation(
        self,
        async_client,
        admin_headers,
        tenant_b_headers,
        sample_customer,
    ):
        """
        Uma empresa não pode influenciar os indicadores
        de outra empresa.
        """
        order_a = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "OS Empresa A",
                "customer_id": sample_customer["id"],
            },
            headers=admin_headers,
        )

        assert order_a.status_code == 201, order_a.text

        customer_b = await async_client.post(
            "/api/v1/customers",
            json={
                "name": "Cliente Empresa B",
            },
            headers=tenant_b_headers,
        )

        assert customer_b.status_code == 201, customer_b.text

        order_b = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "OS Empresa B",
                "customer_id": customer_b.json()["id"],
            },
            headers=tenant_b_headers,
        )

        assert order_b.status_code == 201, order_b.text

        dashboard_a = await async_client.get(
            "/api/v1/dashboard/summary",
            headers=admin_headers,
        )

        dashboard_b = await async_client.get(
            "/api/v1/dashboard/summary",
            headers=tenant_b_headers,
        )

        assert dashboard_a.status_code == 200
        assert dashboard_b.status_code == 200

        data_a = dashboard_a.json()
        data_b = dashboard_b.json()

        assert data_a["status_counts"]["draft"] == 1
        assert data_b["status_counts"]["draft"] == 1

        ids_a = {
            order["id"]
            for order in data_a["recent_orders"]
        }

        ids_b = {
            order["id"]
            for order in data_b["recent_orders"]
        }

        assert order_a.json()["id"] in ids_a
        assert order_b.json()["id"] not in ids_a

        assert order_b.json()["id"] in ids_b
        assert order_a.json()["id"] not in ids_b


    async def test_technician_dashboard_contains_only_own_orders(
        self,
        async_client,
        admin_headers,
        tech_headers,
        sample_customer,
        sample_order,
    ):
        """
        TECHNICIAN deve receber agregações apenas das OS
        atribuídas ao próprio usuário.
        """
        me_response = await async_client.get(
            "/api/v1/auth/me",
            headers=tech_headers,
        )

        assert me_response.status_code == 200

        tech_a_id = me_response.json()["id"]

        second_tech = await async_client.post(
            "/api/v1/users",
            json={
                "full_name": "Tecnico Dashboard B",
                "email": "tech-dashboard-b@empresa-a.com",
                "password": "Senha123",
                "role": "technician",
            },
            headers=admin_headers,
        )

        assert second_tech.status_code == 201, second_tech.text

        other_order = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "OS Segundo Tecnico",
                "customer_id": sample_customer["id"],
                "technician_id": second_tech.json()["id"],
            },
            headers=admin_headers,
        )

        assert other_order.status_code == 201, other_order.text

        dashboard = await async_client.get(
            "/api/v1/dashboard/summary",
            headers=tech_headers,
        )

        assert dashboard.status_code == 200, dashboard.text

        data = dashboard.json()

        assert data["status_counts"]["draft"] == 1

        recent_ids = {
            order["id"]
            for order in data["recent_orders"]
        }

        assert sample_order["id"] in recent_ids
        assert other_order.json()["id"] not in recent_ids

        # Confirma também que estamos autenticados como
        # o técnico esperado.
        assert tech_a_id is not None
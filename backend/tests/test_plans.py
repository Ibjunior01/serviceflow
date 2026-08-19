from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.models.company import Company

from app.models.company import Company, PlanTier
from app.models.subscription import SubscriptionStatus

class TestTrial:
    async def test_new_company_starts_with_pro_trial(
        self,
        async_client,
        owner_headers,
    ):
        r = await async_client.get(
            "/api/v1/companies/me",
            headers=owner_headers,
        )

        assert r.status_code == 200, r.text

        data = r.json()

        assert data["plan_tier"] == "pro"
        assert data["subscription_status"] == "trialing"
        assert data["trial_ends_at"] is not None

        trial_ends_at = datetime.fromisoformat(
            data["trial_ends_at"].replace("Z", "+00:00")
        )

        now = datetime.now(timezone.utc)
        remaining = trial_ends_at - now

        # Evita um teste frágil por diferença de alguns segundos.
        assert timedelta(days=13, hours=23) <= remaining
        assert remaining <= timedelta(days=14, hours=1)

    async def test_expired_trial_downgrades_company_to_free(
        self,
        async_client,
        owner_headers,
        db_session,
    ):
        company_r = await async_client.get(
            "/api/v1/companies/me",
            headers=owner_headers,
        )

        assert company_r.status_code == 200, company_r.text

        company_id = UUID(company_r.json()["id"])

        company = await db_session.get(
            Company,
            company_id,
        )

        assert company is not None
        assert company.subscription is not None

        # Simula que o trial terminou.
        company.subscription.trial_ends_at = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        )

        await db_session.commit()

        # Qualquer endpoint autenticado chama get_current_user(),
        # que aplica a regra de expiração do trial.
        r = await async_client.get(
            "/api/v1/companies/me",
            headers=owner_headers,
        )

        assert r.status_code == 200, r.text

        data = r.json()

        assert data["plan_tier"] == "free"
        assert data["subscription_status"] == "active"

class TestFreePlanLimits:
    async def _force_free_plan(
        self,
        async_client,
        owner_headers,
        db_session,
    ):
        company_r = await async_client.get(
            "/api/v1/companies/me",
            headers=owner_headers,
        )
        assert company_r.status_code == 200, company_r.text

        company_id = UUID(company_r.json()["id"])

        company = await db_session.get(
            Company,
            company_id,
        )

        assert company is not None
        assert company.subscription is not None

        company.plan_tier = PlanTier.FREE
        company.subscription.plan_tier = PlanTier.FREE
        company.subscription.status = SubscriptionStatus.ACTIVE
        company.subscription.trial_ends_at = None

        await db_session.commit()

        return company

    async def test_free_plan_allows_only_one_technician(
        self,
        async_client,
        owner_headers,
        db_session,
    ):
        await self._force_free_plan(
            async_client,
            owner_headers,
            db_session,
        )

        first_r = await async_client.post(
            "/api/v1/users",
            json={
                "full_name": "Tecnico Free 1",
                "email": "tech-free-1@test.com",
                "password": "Senha123",
                "role": "technician",
            },
            headers=owner_headers,
        )

        assert first_r.status_code == 201, first_r.text

        second_r = await async_client.post(
            "/api/v1/users",
            json={
                "full_name": "Tecnico Free 2",
                "email": "tech-free-2@test.com",
                "password": "Senha123",
                "role": "technician",
            },
            headers=owner_headers,
        )

        assert second_r.status_code == 403, second_r.text

        usage_r = await async_client.get(
            "/api/v1/companies/me/usage",
            headers=owner_headers,
        )

        assert usage_r.status_code == 200, usage_r.text

        usage = usage_r.json()

        assert usage["technicians_used"] == 1
        assert usage["technicians_limit"] == 1

    async def test_free_plan_allows_only_five_customers(
        self,
        async_client,
        owner_headers,
        db_session,
    ):
        await self._force_free_plan(
            async_client,
            owner_headers,
            db_session,
        )

        for number in range(1, 6):
            r = await async_client.post(
                "/api/v1/customers",
                json={
                    "name": f"Cliente Free {number}",
                    "email": f"cliente-free-{number}@test.com",
                },
                headers=owner_headers,
            )

            assert r.status_code == 201, r.text

        blocked_r = await async_client.post(
            "/api/v1/customers",
            json={
                "name": "Cliente Free 6",
                "email": "cliente-free-6@test.com",
            },
            headers=owner_headers,
        )

        assert blocked_r.status_code == 403, blocked_r.text

        usage_r = await async_client.get(
            "/api/v1/companies/me/usage",
            headers=owner_headers,
        )

        assert usage_r.status_code == 200, usage_r.text

        usage = usage_r.json()

        assert usage["customers_used"] == 5
        assert usage["customers_limit"] == 5

    async def test_free_plan_allows_only_ten_orders_per_month(
        self,
        async_client,
        owner_headers,
        db_session,
    ):
        await self._force_free_plan(
            async_client,
            owner_headers,
            db_session,
        )

        customer_r = await async_client.post(
            "/api/v1/customers",
            json={
                "name": "Cliente das OS Free",
                "email": "cliente-os-free@test.com",
            },
            headers=owner_headers,
        )

        assert customer_r.status_code == 201, customer_r.text

        customer_id = customer_r.json()["id"]

        for number in range(1, 11):
            r = await async_client.post(
                "/api/v1/orders",
                json={
                    "title": f"Ordem Free {number}",
                    "customer_id": customer_id,
                },
                headers=owner_headers,
            )

            assert r.status_code == 201, r.text

        blocked_r = await async_client.post(
            "/api/v1/orders",
            json={
                "title": "Ordem Free 11",
                "customer_id": customer_id,
            },
            headers=owner_headers,
        )

        assert blocked_r.status_code == 403, blocked_r.text

        usage_r = await async_client.get(
            "/api/v1/companies/me/usage",
            headers=owner_headers,
        )

        assert usage_r.status_code == 200, usage_r.text

        usage = usage_r.json()

        assert usage["orders_this_month_used"] == 10
        assert usage["orders_this_month_limit"] == 10
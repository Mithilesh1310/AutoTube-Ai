import asyncio
import httpx
from backend.main import app

async def test_billing():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch plans
        res = await client.get("/api/v1/billing/plans")
        assert res.status_code == 200, f"Plans failed: {res.text}"
        plans = res.json()["plans"]
        assert "STARTER" in plans and "PRO" in plans and "AGENCY" in plans
        print("[PASS] Plans API returned all tiers (Starter, Pro, Agency)")

        # 2. Create Checkout Session (USD)
        res_checkout = await client.post("/api/v1/billing/create-checkout-session", json={
            "plan_tier": "PRO",
            "billing_cycle": "MONTHLY",
            "currency": "USD",
            "gateway": "STRIPE",
            "user_id": 1
        })
        assert res_checkout.status_code == 200, f"Checkout failed: {res_checkout.text}"
        data = res_checkout.json()
        assert data["amount"] == 79
        print("[PASS] Checkout session created for PRO Tier ($79/mo)")

        # 3. Create Checkout Session (INR & Razorpay)
        res_rzp = await client.post("/api/v1/billing/create-checkout-session", json={
            "plan_tier": "PRO",
            "billing_cycle": "ANNUAL",
            "currency": "INR",
            "gateway": "RAZORPAY",
            "user_id": 1
        })
        assert res_rzp.status_code == 200, f"Razorpay Checkout failed: {res_rzp.text}"
        data_rzp = res_rzp.json()
        assert data_rzp["amount"] == 56999
        print("[PASS] Razorpay INR Annual Checkout created (₹56,999/yr)")

        # 4. Verify Payment / Activate Subscription
        res_verify = await client.post("/api/v1/billing/verify-payment", json={
            "user_id": 1,
            "plan_tier": "PRO",
            "billing_cycle": "MONTHLY",
            "currency": "USD",
            "gateway": "STRIPE",
            "transaction_id": "test_tx_pro_12345",
            "amount": 79.0
        })
        assert res_verify.status_code == 200, f"Verify failed: {res_verify.text}"
        print(f"[PASS] Subscription verification succeeded: {res_verify.json()['message']}")

        # 5. Check Subscription Status
        res_status = await client.get("/api/v1/billing/subscription-status?user_id=1")
        assert res_status.status_code == 200, f"Status failed: {res_status.text}"
        status_data = res_status.json()
        assert status_data["plan_tier"] == "PRO"
        assert status_data["limits"]["max_channels"] == 3
        print(f"[PASS] Active plan verified: {status_data['plan_name']} with {status_data['limits']['max_channels']} channels limit!")

if __name__ == "__main__":
    asyncio.run(test_billing())

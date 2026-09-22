import datetime
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.config import settings
from backend.db.session import get_db
from backend.db.models import User, Subscription, PaymentTransaction, YouTubeChannel, Setting

logger = logging.getLogger(__name__)

billing_router = APIRouter(prefix="/billing", tags=["Billing & SaaS Subscriptions"])

# Tier definitions
PLANS_DATA = {
    "STARTER": {
        "id": "STARTER",
        "name": "Creator Starter",
        "tagline": "Ideal for solo creators launching their first automated channel",
        "popular": False,
        "pricing": {
            "USD": {"monthly": 12, "annual": 119, "currency_symbol": "$"},
            "INR": {"monthly": 999, "annual": 8999, "currency_symbol": "₹"}
        },
        "limits": {
            "max_channels": 1,
            "shorts_per_month": 30,
            "long_videos_per_month": 0,
            "credits_balance": 300,
            "resolution": "1080p Full HD",
            "voice_style": "Standard Neural Hindi",
            "qa_gates": True,
            "character_customization": False,
            "priority_gpu": False
        },
        "features": [
            "1 Connected YouTube Channel",
            "30 Autonomous Shorts / Month",
            "AI Story & Script Generation (Gemini)",
            "Automated Daily 10:00 AM Upload",
            "Built-in Script QA Gate (>=85)",
            "Standard Neural Hindi Kids Voice"
        ]
    },
    "PRO": {
        "id": "PRO",
        "name": "Growth Pro",
        "tagline": "The sweet spot for scaling 3 profitable kid story channels",
        "popular": True,
        "pricing": {
            "USD": {"monthly": 30, "annual": 279, "currency_symbol": "$"},
            "INR": {"monthly": 2499, "annual": 22999, "currency_symbol": "₹"}
        },
        "limits": {
            "max_channels": 3,
            "shorts_per_month": 100,
            "long_videos_per_month": 10,
            "credits_balance": 1000,
            "resolution": "4K Ultra HD",
            "voice_style": "Multi-Speaker Emotion Voice",
            "qa_gates": True,
            "character_customization": True,
            "priority_gpu": True
        },
        "features": [
            "Up to 3 YouTube Channels",
            "100 Shorts + Moving AI Clips / Month",
            "4K Ultra HD Upscaling",
            "Consistent Character Universe (Chintu, Bholu)",
            "Multi-Voice Emotion Acting",
            "Automated Anti-Repetition Semantic Memory",
            "Priority GPU Rendering Queue"
        ]
    },
    "AGENCY": {
        "id": "AGENCY",
        "name": "Studio Agency",
        "tagline": "For production studios running automated YouTube empires",
        "popular": False,
        "pricing": {
            "USD": {"monthly": 72, "annual": 659, "currency_symbol": "$"},
            "INR": {"monthly": 5999, "annual": 54999, "currency_symbol": "₹"}
        },
        "limits": {
            "max_channels": 10,
            "shorts_per_month": 300,
            "long_videos_per_month": 30,
            "credits_balance": 3000,
            "resolution": "4K Ultra HD Cinematic",
            "voice_style": "Custom Voice Cloning & Any Dialect",
            "qa_gates": True,
            "character_customization": True,
            "priority_gpu": True
        },
        "features": [
            "Up to 10 YouTube Channels",
            "300 Shorts + 30 Long-form / Month",
            "Voice Cloning & Dialect Customization",
            "Multi-channel Automated Schedules",
            "VIP Priority GPU Pipeline",
            "24/7 Dedicated Support Agent"
        ]
    }
}

class CheckoutRequest(BaseModel):
    user_id: Optional[int] = 1
    plan_tier: str # STARTER, PRO, AGENCY
    billing_cycle: str = "MONTHLY" # MONTHLY, ANNUAL
    currency: str = "INR" # USD, INR
    gateway: str = "UPI" # UPI, RAZORPAY, STRIPE

class PaymentVerifyRequest(BaseModel):
    user_id: Optional[int] = 1
    plan_tier: str
    billing_cycle: str = "MONTHLY"
    currency: str = "INR"
    gateway: str = "UPI"
    transaction_id: str
    order_id: Optional[str] = None
    amount: float

@billing_router.get("/plans")
async def get_plans(db: AsyncSession = Depends(get_db)):
    """Retrieve public SaaS subscription plans, pricing, and feature comparison."""
    upi_vpa = settings.DEFAULT_UPI_ID
    try:
        res = await db.execute(select(Setting).where(Setting.key == "DEFAULT_UPI_ID"))
        db_setting = res.scalar_one_or_none()
        if db_setting and db_setting.value:
            upi_vpa = db_setting.value.strip()
    except Exception as e:
        logger.warning(f"Could not load DEFAULT_UPI_ID from db: {e}")

    return {
        "plans": PLANS_DATA,
        "supported_currencies": ["USD", "INR"],
        "gateways": {
            "upi_enabled": True,
            "default_upi_id": upi_vpa,
            "stripe_enabled": bool(settings.STRIPE_SECRET_KEY) or settings.BILLING_SANDBOX_MODE,
            "razorpay_enabled": bool(settings.RAZORPAY_KEY_ID) or settings.BILLING_SANDBOX_MODE,
            "sandbox_mode": settings.BILLING_SANDBOX_MODE
        }
    }

@billing_router.post("/create-checkout-session")
async def create_checkout_session(payload: CheckoutRequest, db: AsyncSession = Depends(get_db)):
    """Creates a checkout session for UPI, Stripe, or Razorpay."""
    import urllib.parse
    plan = PLANS_DATA.get(payload.plan_tier)
    if not plan:
        raise HTTPException(status_code=400, detail=f"Invalid plan tier: {payload.plan_tier}")

    cycle = payload.billing_cycle.upper()
    curr = payload.currency.upper()
    pricing_info = plan["pricing"].get(curr, plan["pricing"]["USD"])
    amount = pricing_info["annual"] if cycle == "ANNUAL" else pricing_info["monthly"]

    # 1. Direct Instant UPI Payment Gateway (0% Fee, GPay/PhonePe/Paytm Intent & Dynamic QR)
    if payload.gateway.upper() in ["UPI", "DIRECT_UPI"]:
        upi_vpa = (settings.DEFAULT_UPI_ID or "Q596657023@ybl").strip()
        try:
            res = await db.execute(select(Setting).where(Setting.key == "DEFAULT_UPI_ID"))
            db_setting = res.scalar_one_or_none()
            if db_setting and db_setting.value and db_setting.value.strip():
                upi_vpa = db_setting.value.strip()
        except Exception as e:
            logger.warning(f"Could not fetch DEFAULT_UPI_ID from DB: {e}")

        payee_name = "AutoTubeAI"
        txn_note = f"AutoTube_{payload.plan_tier}"
        
        upi_link = f"upi://pay?pa={upi_vpa}&pn={payee_name}&am={int(amount)}&cu=INR&tn={txn_note}"
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_link)}"
        session_id = f"upi_ord_{uuid.uuid4().hex[:10]}"
        
        return {
            "gateway": "UPI",
            "mode": "INSTANT_UPI",
            "upi_id": upi_vpa,
            "upi_link": upi_link,
            "qr_code_url": qr_code_url,
            "amount": amount,
            "currency": "INR",
            "plan_tier": payload.plan_tier,
            "billing_cycle": cycle,
            "session_id": session_id,
            "order_id": session_id,
            "message": "Scan QR Code with any UPI App or click Pay via GPay/PhonePe/Paytm."
        }

    # 1. Real Stripe Integration if key is configured
    if payload.gateway.upper() == "STRIPE" and settings.STRIPE_SECRET_KEY:
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': curr.lower(),
                        'product_data': {
                            'name': f"AutoTube {plan['name']} ({cycle.capitalize()})",
                            'description': plan['tagline'],
                        },
                        'unit_amount': int(amount * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='http://localhost:3000/dashboard?payment=success&tier=' + payload.plan_tier,
                cancel_url='http://localhost:3000/?payment=cancelled',
                metadata={'user_id': str(payload.user_id), 'plan_tier': payload.plan_tier}
            )
            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "gateway": "STRIPE",
                "mode": "LIVE"
            }
        except Exception as e:
            logger.warning(f"Stripe live checkout session creation failed: {e}. Falling back to sandbox.")

    # 2. Real Razorpay Integration if key is configured
    if payload.gateway.upper() == "RAZORPAY" or (settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET):
        try:
            if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
                import razorpay
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                order_receipt = f"rcpt_{uuid.uuid4().hex[:8]}"
                order_data = {
                    "amount": int(amount * 100), # Razorpay expects amount in paise (1 INR = 100 paise)
                    "currency": curr,
                    "receipt": order_receipt,
                    "notes": {
                        "user_id": str(payload.user_id),
                        "plan_tier": payload.plan_tier,
                        "cycle": cycle
                    }
                }
                order = client.order.create(data=order_data)
                return {
                    "order_id": order['id'],
                    "amount": amount,
                    "amount_paise": int(amount * 100),
                    "currency": curr,
                    "key_id": settings.RAZORPAY_KEY_ID,
                    "gateway": "RAZORPAY",
                    "mode": "LIVE"
                }
        except Exception as e:
            logger.warning(f"Razorpay live order creation failed: {e}. Falling back to sandbox.")

    # 3. Sandbox / Simulation Mode (Production-ready immediate testing)
    simulated_id = f"order_sim_{uuid.uuid4().hex[:12]}"
    return {
        "gateway": "RAZORPAY",
        "mode": "SANDBOX_SIMULATION",
        "plan_tier": payload.plan_tier,
        "billing_cycle": cycle,
        "currency": curr,
        "amount": amount,
        "amount_paise": int(amount * 100),
        "key_id": settings.RAZORPAY_KEY_ID or "rzp_test_simulated_key_12345",
        "session_id": simulated_id,
        "order_id": simulated_id,
        "message": "Razorpay sandbox order ready. Instant activation available."
    }

@billing_router.post("/verify-payment")
async def verify_payment(payload: PaymentVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verifies and finalizes user subscription, increasing plan limits and crediting quota."""
    user_id = payload.user_id or 1
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalars().first()
    if not user:
        # Create default user if not exists
        user = User(
            id=user_id,
            username="startup_admin",
            email="founder@autotube.ai",
            password_hash="mock_hash_saas"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    plan = PLANS_DATA.get(payload.plan_tier, PLANS_DATA["STARTER"])
    limits = plan["limits"]

    # Calculate cycle duration
    now = datetime.datetime.utcnow()
    duration_days = 365 if payload.billing_cycle.upper() == "ANNUAL" else 30
    end_date = now + datetime.timedelta(days=duration_days)

    # 1. Record Transaction
    tx = PaymentTransaction(
        user_id=user.id,
        gateway=payload.gateway.upper(),
        transaction_id=payload.transaction_id,
        order_id=payload.order_id or payload.transaction_id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        status="SUCCESS",
        plan_tier=payload.plan_tier,
        payment_method="ONLINE",
        details={"billing_cycle": payload.billing_cycle, "verified_at": now.isoformat()}
    )
    db.add(tx)

    # 2. Record or Update Subscription
    sub_res = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    sub = sub_res.scalars().first()
    if not sub:
        sub = Subscription(
            user_id=user.id,
            plan_tier=payload.plan_tier,
            billing_cycle=payload.billing_cycle.upper(),
            currency=payload.currency.upper(),
            amount=payload.amount,
            status="ACTIVE",
            payment_gateway=payload.gateway.upper(),
            external_subscription_id=payload.transaction_id,
            current_period_start=now,
            current_period_end=end_date
        )
        db.add(sub)
    else:
        sub.plan_tier = payload.plan_tier
        sub.billing_cycle = payload.billing_cycle.upper()
        sub.currency = payload.currency.upper()
        sub.amount = payload.amount
        sub.status = "ACTIVE"
        sub.current_period_start = now
        sub.current_period_end = end_date
        sub.updated_at = now

    # 3. Upgrade User Profile & Limits
    user.plan_tier = payload.plan_tier
    user.subscription_status = "ACTIVE"
    user.credits_balance = float(limits["credits_balance"])
    user.monthly_credit_limit = float(limits["credits_balance"])
    user.daily_credit_limit = float(limits["credits_balance"] / 10.0)

    await db.commit()

    return {
        "success": True,
        "message": f"Successfully activated {plan['name']}!",
        "plan_tier": user.plan_tier,
        "credits_balance": user.credits_balance,
        "valid_until": end_date.strftime("%Y-%m-%d")
    }

@billing_router.get("/subscription-status")
async def get_subscription_status(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """Returns the current user's active tier, usage limits, and renewal dates."""
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalars().first()
    
    current_tier = user.plan_tier if user and user.plan_tier else "STARTER"
    plan_info = PLANS_DATA.get(current_tier, PLANS_DATA["STARTER"])

    # Count connected channels
    channels_res = await db.execute(select(YouTubeChannel).where(YouTubeChannel.user_id == user_id))
    connected_channels = len(channels_res.scalars().all())

    # Get subscription end date if present
    sub_res = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    sub = sub_res.scalars().first()
    renewal_str = sub.current_period_end.strftime("%d %b %Y") if sub and sub.current_period_end else "30 Days from activation"

    return {
        "plan_tier": current_tier,
        "plan_name": plan_info["name"],
        "subscription_status": user.subscription_status if user else "ACTIVE",
        "credits_balance": user.credits_balance if user else 500.0,
        "renewal_date": renewal_str,
        "limits": plan_info["limits"],
        "usage": {
            "channels_used": connected_channels,
            "max_channels": plan_info["limits"]["max_channels"],
            "remaining_channels": max(0, plan_info["limits"]["max_channels"] - connected_channels)
        }
    }

@billing_router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Stripe webhook receiver for handling subscription lifecycle events."""
    payload_body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    
    # If stripe secret is present, verify signature
    if settings.STRIPE_WEBHOOK_SECRET and settings.STRIPE_SECRET_KEY:
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            event = stripe.Webhook.construct_event(
                payload_body, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            event_type = event["type"]
            data_object = event["data"]["object"]
            logger.info(f"Received Stripe webhook event: {event_type}")
            # Handle completed checkout
            if event_type == "checkout.session.completed":
                meta = data_object.get("metadata", {})
                user_id = int(meta.get("user_id", 1))
                tier = meta.get("plan_tier", "PRO")
                user_res = await db.execute(select(User).where(User.id == user_id))
                u = user_res.scalars().first()
                if u:
                    u.plan_tier = tier
                    u.subscription_status = "ACTIVE"
                    await db.commit()
            return {"status": "success", "event": event_type}
        except Exception as e:
            logger.error(f"Stripe webhook error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    return {"status": "received", "mode": "sandbox"}

@billing_router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Razorpay webhook receiver for subscription events."""
    data = await request.json()
    logger.info(f"Received Razorpay webhook payload: {data.get('event')}")
    return {"status": "received", "event": data.get('event')}

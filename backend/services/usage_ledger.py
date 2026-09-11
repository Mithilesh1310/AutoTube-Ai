import logging
from typing import Optional
from backend.db.session import AsyncSessionLocal
from backend.db.models import UsageLedger, User
from sqlalchemy import update

logger = logging.getLogger(__name__)

class UsageLedgerService:
    """
    Backend-Authoritative Usage & Billing Ledger:
    Creates immutable database records for every AI API provider call and updates user credit balances.
    """
    @staticmethod
    async def record_usage(
        user_id: int,
        channel_id: Optional[int],
        job_id: Optional[str],
        provider_name: str,
        model_name: str,
        operation_type: str,
        estimated_cost: float,
        actual_cost: float,
        credits_used: float
    ):
        async with AsyncSessionLocal() as session:
            ledger_entry = UsageLedger(
                user_id=user_id,
                channel_id=channel_id,
                job_id=job_id,
                provider_name=provider_name,
                model_name=model_name,
                operation_type=operation_type,
                estimated_cost=estimated_cost,
                actual_cost=actual_cost,
                credits_used=credits_used
            )
            session.add(ledger_entry)

            # Deduct credits from user balance
            if credits_used > 0:
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(credits_balance=User.credits_balance - credits_used)
                )

            await session.commit()
            logger.info(f"[UsageLedger] Logged {operation_type} call via '{provider_name}' (Cost: ${actual_cost:.4f}, Credits: {credits_used}).")

usage_ledger_service = UsageLedgerService()

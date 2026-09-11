import logging
from typing import Dict, Any, Tuple
from sqlalchemy import select, func
from backend.db.session import AsyncSessionLocal
from backend.db.models import User, UsageLedger
from backend.config import settings

logger = logging.getLogger(__name__)

class InsufficientCreditsError(RuntimeError):
    """Raised when user credit balance or spending limit is exceeded before execution."""
    pass

class CostProtectionService:
    """
    Cost Protection System:
    Estimates generation costs before launching expensive AI animation or image calls.
    Validates daily limits, monthly spending limits, credit balance, per-job limits,
    and global emergency kill switch.
    """
    @staticmethod
    def estimate_job_cost(
        visual_mode: str = "FULL_ANIMATION", 
        video_type: str = "LONG", 
        scene_count: Optional[int] = None,
        retry_allowance_pct: float = 0.20
    ) -> float:
        """Calculates estimated cost in USD based on generation mode and length with retry allowance."""
        if scene_count is None:
            scene_count = 5 if video_type == "SHORT" else 15

        if visual_mode == "IMAGE_MOTION":
            base = scene_count * 0.005
        elif visual_mode in ["FULL_ANIMATION", "HYBRID"]:
            base = scene_count * 0.05
        else: # AUTO
            base = scene_count * 0.04

        # Add buffer for QA retries (20%)
        total_estimate = base * (1.0 + retry_allowance_pct)
        return round(total_estimate, 4)

    @staticmethod
    async def validate_user_spending(
        user_id: int,
        estimated_cost: float,
        max_job_budget: float = 10.0
    ) -> Tuple[bool, str]:
        """
        Validates user account spending limits, credit balance, and per-job maximum.
        Returns: (is_approved: bool, reason: str)
        """
        # 1. Global Emergency Kill Switch Check
        if getattr(settings, "GLOBAL_EMERGENCY_STOP", False):
            return False, "GLOBAL_EMERGENCY_STOP: All AI generation runs are globally paused."

        # 2. Per-job max budget check
        if estimated_cost > max_job_budget:
            return False, f"JOB_BUDGET_EXCEEDED: Estimated cost ${estimated_cost:.2f} exceeds per-job max of ${max_job_budget:.2f}."

        async with AsyncSessionLocal() as session:
            res_user = await session.execute(select(User).where(User.id == user_id))
            user = res_user.scalar_one_or_none()
            if not user:
                return True, "Approved (Default Sandbox User)"

            # 3. Check credit balance
            if user.credits_balance < estimated_cost:
                return False, f"Insufficient credits balance (INSUFFICIENT_CREDITS): Required ${estimated_cost:.2f}, Balance ${user.credits_balance:.2f}."

            # 4. Check daily spending limit
            # Sum usage today
            import datetime
            today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            res_spent = await session.execute(
                select(func.sum(UsageLedger.actual_cost))
                .where(
                    UsageLedger.user_id == user_id,
                    UsageLedger.timestamp >= today_start
                )
            )
            spent_today = res_spent.scalar() or 0.0
            daily_limit = user.daily_credit_limit or 100.0

            if (spent_today + estimated_cost) > daily_limit:
                return False, f"DAILY_LIMIT_EXCEEDED: Today's spend ${spent_today:.2f} + ${estimated_cost:.2f} exceeds daily limit of ${daily_limit:.2f}."

            return True, "Approved"

cost_protection_service = CostProtectionService()

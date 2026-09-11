import logging
from typing import Dict, Any
from pydantic import BaseModel
from sqlalchemy import update
from backend.db.session import AsyncSessionLocal
from backend.db.models import ContentIdea
from backend.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

class SelectionResponse(BaseModel):
    selected_index: int
    selection_reason: str

async def run_planner_agent(state_dict: dict) -> dict:
    logger.info("[PlannerAgent] Running Content Planner Agent...")
    candidates = state_dict.get("candidate_ideas", [])
    
    if not candidates:
        raise ValueError("No candidate ideas available for Content Planner Agent.")

    prompt = f"""
You are the Content Planner Agent for 'AutoTube' (Hindi Kids YouTube Channel).
Review these candidate ideas and select the single best one for today's video production:

Candidates:
{candidates}

Select the candidate that will achieve highest child engagement, strong emotional/funny hook, and positive message.
Return JSON with 'selected_index' (0-indexed) and 'selection_reason'.
"""

    try:
        res_obj, meta = gemini_service.generate_structured(
            prompt=prompt,
            response_schema=SelectionResponse,
            system_instruction="Select the optimal children's video topic.",
            temperature=0.3
        )
        idx = res_obj.selected_index if 0 <= res_obj.selected_index < len(candidates) else 0
        selected = candidates[idx]
        selected["selection_reason"] = res_obj.selection_reason
    except Exception as e:
        logger.warning(f"Planner fallback: {e}")
        selected = candidates[0]
        selected["selection_reason"] = "Selected highest scoring default candidate."

    # Update DB status
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(ContentIdea)
            .where(ContentIdea.topic_title == selected["topic_title"])
            .values(is_selected=True)
        )
        await session.commit()

    state_dict["selected_idea"] = selected
    state_dict["current_step"] = "SCRIPT_WRITER"
    state_dict["logs"].append({
        "agent": "PlannerAgent",
        "level": "SUCCESS",
        "message": f"Selected topic: '{selected['topic_title']}'."
    })
    return state_dict

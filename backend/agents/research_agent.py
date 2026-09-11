import logging
import json
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy import select
from backend.db.session import AsyncSessionLocal
from backend.db.models import ContentIdea, Video
from backend.services.gemini_service import gemini_service
from backend.services.character_bible import character_bible

logger = logging.getLogger(__name__)

class IdeaCandidate(BaseModel):
    topic_title: str
    summary: str
    category: str
    conflict_type: str = Field(..., description="e.g. Lost item, Mystery puzzle, Playful competition, Environmental challenge")
    resolution_type: str = Field(..., description="e.g. Clever invention, Teamwork coordination, Wise advice, Kindness gesture")
    target_audience: str = "Kids 3-10"
    reasoning: str

class ResearchResponse(BaseModel):
    ideas: List[IdeaCandidate]

async def run_research_agent(state_dict: dict) -> dict:
    logger.info("[ResearchAgent] Running Content Variety Research Agent...")
    
    existing_titles = []
    recent_summaries = []
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ContentIdea.topic_title, ContentIdea.summary).limit(30))
        rows = result.fetchall()
        existing_titles = [r[0] for r in rows]
        recent_summaries = [r[1] for r in rows if r[1]]

    characters = await character_bible.get_all_characters()
    chars_str = ", ".join([f"{c['name']} ({c['species']} - {c['personality']})" for c in characters])

    prompt = f"""
You are the Lead Content Strategy Research Agent for 'AutoTube' (Hindi Kids YouTube Channel).
Character Universe available: {chars_str}.

CONTENT VARIETY PROTECTION RULE:
Analyze recent story premises:
{json.dumps(recent_summaries[-5:]) if recent_summaries else "None yet"}

DO NOT repeat similar conflict patterns (e.g. if recent video was 'Character trapped in bush → friends rescue', avoid repeating the trapped-rescue formula).
Diversify story types across: Mystery solving, Playful competition, Invention/creativity, Friendship misunderstandings, Nature exploration.

DO NOT duplicate these previously created topics:
{json.dumps(existing_titles) if existing_titles else "None yet"}

Generate 4 unique, creative, highly engaging Hindi kids cartoon story ideas with distinct conflict and resolution types.
Return structured JSON.
"""

    system_instruction = "You are an expert children's content researcher and YouTube audience growth strategist."

    try:
        res_obj, meta = gemini_service.generate_structured(
            prompt=prompt,
            response_schema=ResearchResponse,
            system_instruction=system_instruction,
            temperature=0.85
        )
        candidates = [idea.model_dump() for idea in res_obj.ideas]
        state_dict["research_is_fallback"] = False
        state_dict["verification_status"] = "LIVE_API_VERIFIED"
    except Exception as e:
        logger.warning(f"[ResearchAgent] Gemini API fallback: {e}")
        candidates = [
            {
                "topic_title": "तितू की उड़ने वाली नाव की खोज (Titu's Flying Boat Quest)",
                "summary": "तितू को नदी किनारे एक पुरानी लकड़ी की नाव मिलती है जिसे दोस्तों के साथ मिलकर नया रूप दिया जाता है।",
                "category": "Invention & Creativity",
                "conflict_type": "Environmental challenge",
                "resolution_type": "Teamwork coordination",
                "target_audience": "Kids 3-10",
                "reasoning": "Promotes hands-on creativity and teamwork."
            },
            {
                "topic_title": "मोमो और छुपा हुआ नक्शा (Momo and the Hidden Map)",
                "summary": "मोमो को बरगद के पेड़ के नीचे एक पहेली भरा नक्शा मिलता है जो एक मजेदार सरप्राइज़ तक ले जाता है।",
                "category": "Mystery puzzle",
                "conflict_type": "Mystery puzzle",
                "resolution_type": "Clever thinking",
                "target_audience": "Kids 3-10",
                "reasoning": "High curiosity mystery adventure."
            }
        ]
        state_dict["research_is_fallback"] = True
        state_dict["verification_status"] = "TESTED_WITH_FALLBACK"

    # Save candidates to DB
    async with AsyncSessionLocal() as session:
        for c in candidates:
            idea_obj = ContentIdea(
                topic_title=c["topic_title"],
                summary=c["summary"],
                category=c["category"],
                target_audience=c["target_audience"],
                reasoning=c["reasoning"],
                is_selected=False
            )
            session.add(idea_obj)
        await session.commit()

    state_dict["candidate_ideas"] = candidates
    state_dict["ideas"] = candidates
    state_dict["current_step"] = "PLANNER"
    state_dict["logs"].append({
        "agent": "ResearchAgent",
        "level": "SUCCESS",
        "message": f"Generated {len(candidates)} diverse content ideas."
    })
    return state_dict

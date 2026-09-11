import logging
from pydantic import BaseModel
from typing import List
from backend.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

class MetadataResponse(BaseModel):
    title: str
    description: str
    tags: List[str]
    hashtags: List[str]
    category: str = "15" # Pets & Animals or Film & Animation
    language: str = "hi"

async def run_metadata_agent(state_dict: dict) -> dict:
    logger.info("[MetadataSEO] Running Metadata SEO Agent...")
    script_data = state_dict.get("script_data", {})
    video_type = state_dict.get("video_type", "LONG")

    prompt = f"""
Generate SEO-optimized YouTube Metadata for a Hindi Kids Cartoon Video ({video_type}):

Title Idea: {script_data.get('title_idea')}
Story Summary: {script_data.get('story_summary')}
Moral: {script_data.get('moral')}

Requirements:
1. Title: Catchy, child-friendly Hindi title with emoji (max 80 chars).
2. Description: 3-4 paragraphs in Hindi summarizing the story, character credits, and hashtags.
3. Tags: 12-18 relevant Hindi/English tags (e.g. "Hindi Kids Story", "Chintu Elephant", "Hindi Moral Stories", "Cartoon for kids").
4. Hashtags: 4-6 hashtags (e.g. #HindiStories #KidsCartoons #MoralStories #Chintu #Shorts).

Return structured JSON.
"""

    try:
        res_obj, exec_meta = gemini_service.generate_structured(
            prompt=prompt,
            response_schema=MetadataResponse,
            system_instruction="You are an expert YouTube SEO specialist for Kids Hindi Animation Channels.",
            temperature=0.7
        )
        meta = res_obj.model_dump()
    except Exception as e:
        logger.warning(f"Metadata Agent fallback: {e}")
        meta = {
            "title": f"🐘 {script_data.get('title_idea', 'चिंटू की मजेदार कहानी')} | Hindi Kids Story",
            "description": f"{script_data.get('story_summary', 'बच्चों की सुंदर हिंदी कहानी।')}\n\nनैतिक शिक्षा: {script_data.get('moral', 'हमेशा सच बोलो।')}\n\n#HindiStories #KidsCartoons #Chintu #MoralStories",
            "tags": ["Hindi Kids Story", "Hindi Cartoon", "Moral Stories for Kids", "Chintu", "Momo", "Kids Animation"],
            "hashtags": ["#HindiStories", "#KidsCartoons", "#MoralStories", "#Chintu"],
            "category": "15",
            "language": "hi"
        }

    state_dict["title"] = meta["title"]
    state_dict["description"] = meta["description"]
    state_dict["tags"] = meta["tags"]
    state_dict["hashtags"] = meta["hashtags"]
    state_dict["current_step"] = "THUMBNAIL_GEN"
    state_dict["logs"].append({
        "agent": "MetadataAgent",
        "level": "SUCCESS",
        "message": f"Generated SEO metadata with title: '{meta['title']}'."
    })
    return state_dict

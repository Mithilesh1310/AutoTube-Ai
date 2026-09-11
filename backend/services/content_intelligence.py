import logging
from typing import List, Dict, Any
from sqlalchemy import select
from backend.db.session import AsyncSessionLocal
from backend.db.models import ContentMemory

logger = logging.getLogger(__name__)

class ContentIntelligenceService:
    """
    Per-Channel Content Intelligence:
    Maintains independent memory per channel to track past generated topics, premises, and keywords,
    detecting and rejecting semantic repetition during research.
    """
    @staticmethod
    async def get_recent_channel_topics(channel_id: int, limit: int = 20) -> List[str]:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(ContentMemory.topic_title)
                .where(ContentMemory.channel_id == channel_id)
                .order_by(ContentMemory.created_at.desc())
                .limit(limit)
            )
            return [r[0] for r in res.all()]

    @staticmethod
    async def is_topic_repetitive(channel_id: int, candidate_topic: str) -> bool:
        recent_topics = await ContentIntelligenceService.get_recent_channel_topics(channel_id)
        candidate_words = set(candidate_topic.lower().split())
        
        for past_topic in recent_topics:
            past_words = set(past_topic.lower().split())
            intersection = candidate_words.intersection(past_words)
            # Exclude common stop words
            significant_overlap = [w for w in intersection if len(w) > 3 and w not in ["story", "hindi", "moral"]]
            if len(significant_overlap) >= 2:
                logger.warning(f"[ContentIntelligence] Semantic overlap detected for channel #{channel_id}: '{candidate_topic}' overlaps with '{past_topic}'")
                return True
        return False

    @staticmethod
    async def record_published_topic(channel_id: int, topic_title: str, summary: str, category: str):
        async with AsyncSessionLocal() as session:
            mem = ContentMemory(
                channel_id=channel_id,
                topic_title=topic_title,
                summary=summary,
                category=category
            )
            session.add(mem)
            await session.commit()

content_intelligence_service = ContentIntelligenceService()

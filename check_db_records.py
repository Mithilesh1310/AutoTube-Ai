import sys
import asyncio
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from backend.db.session import AsyncSessionLocal
from backend.db.models import Video, YouTubeChannel
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        res_v = await db.execute(select(Video))
        videos = res_v.scalars().all()
        print(f"Total Videos in DB: {len(videos)}")
        for v in videos:
            print(f"  Video #{v.id}: title='{v.title[:30]}', channel_id={v.channel_id}, user_id={v.user_id}")

        res_c = await db.execute(select(YouTubeChannel))
        channels = res_c.scalars().all()
        print(f"\nTotal Channels in DB: {len(channels)}")
        for c in channels:
            print(f"  Channel #{c.id}: name='{c.channel_name}', yt_id='{c.youtube_channel_id}', user_id={c.user_id}, connected={c.is_connected}")
            if c.profile:
                print(f"    Profile: visual_mode='{c.profile.visual_mode}', format='{c.profile.video_format}', niche='{c.profile.niche}'")

asyncio.run(check())

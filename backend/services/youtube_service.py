import os
import logging
from typing import Optional, Dict, Any
from sqlalchemy import select
from backend.config import settings
from backend.db.session import AsyncSessionLocal
from backend.db.models import Channel, Video

logger = logging.getLogger(__name__)

class YouTubeService:
    @staticmethod
    async def upload_video(
        video_path: str,
        title: str,
        description: str,
        tags: list,
        thumbnail_path: Optional[str] = None,
        publish_mode: str = "UNLISTED",
        is_made_for_kids: bool = True,
        channel_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Uploads video to YouTube via Data API v3 for specific channel or primary channel."""
        
        # Check global emergency kill switch
        if not settings.AGENT_ENABLED:
            logger.warning("AGENT_ENABLED is False. Skipping automated YouTube upload.")
            return {"status": "PAUSED", "reason": "AGENT_ENABLED is disabled in settings."}

        publish_privacy = publish_mode or settings.YOUTUBE_PUBLISH_MODE

        logger.info(f"[YouTubeService] Preparing YouTube Upload for Channel #{channel_id}. File: {video_path}, Privacy: {publish_privacy}")

        # Check OAuth channel token in DB
        async with AsyncSessionLocal() as session:
            channel = None
            if channel_id:
                result = await session.execute(
                    select(Channel).where(Channel.id == channel_id, Channel.is_connected == True)
                )
                channel = result.scalar_one_or_none()
            if not channel:
                result = await session.execute(select(Channel).where(Channel.is_connected == True))
                channel = result.scalar_one_or_none()

        has_channel_token = channel and (
            getattr(channel, "access_token_encrypted", None) or 
            getattr(channel, "refresh_token_encrypted", None) or 
            getattr(channel, "encrypted_access_token", None) or 
            getattr(channel, "encrypted_refresh_token", None)
        )
        has_env_refresh = bool(getattr(settings, "YOUTUBE_REFRESH_TOKEN", None))

        if not has_channel_token and not has_env_refresh:
            if getattr(settings, "TEST_MODE", False):
                logger.warning("TEST_MODE is active and no connected YouTube channel found. Using mock YouTube upload.")
                mock_id = f"yt_demo_{os.path.basename(video_path).split('.')[0]}"
                return {
                    "status": "COMPLETED",
                    "youtube_video_id": mock_id,
                    "youtube_url": f"https://youtu.be/{mock_id}",
                    "privacy": publish_privacy,
                    "note": "Uploaded in testing sandbox mode (OAuth credentials pending connection in Dashboard settings)."
                }

            error_msg = (
                "YouTube Channel is NOT authorized with Google OAuth! "
                "AutoTube cannot upload to your YouTube channel until you grant permission. "
                "Please go to Settings (http://localhost:3000/settings) and click 'Connect Google Account', "
                "or set YOUTUBE_REFRESH_TOKEN in your configuration."
            )
            logger.error(f"[YouTubeService] {error_msg}")
            return {
                "status": "FAILED",
                "error": error_msg,
                "reason": error_msg
            }

        # Real YouTube Data API v3 resumable upload
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            import asyncio

            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found at path: {video_path}")

            from backend.services.security import decrypt_token, encrypt_token
            plain_token = None
            if channel:
                raw_tok = getattr(channel, "access_token_encrypted", None) or getattr(channel, "encrypted_access_token", None)
                if raw_tok:
                    plain_token = decrypt_token(raw_tok)

            plain_refresh = None
            if channel:
                raw_ref = getattr(channel, "refresh_token_encrypted", None) or getattr(channel, "encrypted_refresh_token", None)
                if raw_ref:
                    plain_refresh = decrypt_token(raw_ref)

            if not plain_refresh and getattr(settings, "YOUTUBE_REFRESH_TOKEN", None):
                plain_refresh = settings.YOUTUBE_REFRESH_TOKEN.strip()

            # Construct OAuth credentials from DB or environment
            creds = Credentials(
                token=plain_token,
                refresh_token=plain_refresh,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.YOUTUBE_CLIENT_ID,
                client_secret=settings.YOUTUBE_CLIENT_SECRET,
                scopes=[
                    "https://www.googleapis.com/auth/youtube.upload",
                    "https://www.googleapis.com/auth/youtube.readonly"
                ]
            )

            privacy_status = (publish_privacy or "UNLISTED").lower()
            if privacy_status not in ["public", "private", "unlisted"]:
                privacy_status = "unlisted"

            def _sync_upload():
                # Refresh token if invalid or expired
                if (not creds.valid or creds.expired or not creds.token) and creds.refresh_token:
                    logger.info("[YouTubeService] Access token expired or empty, refreshing with Google OAuth...")
                    creds.refresh(Request())

                youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

                body = {
                    "snippet": {
                        "title": title[:100],
                        "description": description[:5000],
                        "tags": tags[:30] if tags else ["Kids", "Cartoon", "Animation", "HindiStories"],
                        "categoryId": "1" # Film & Animation
                    },
                    "status": {
                        "privacyStatus": privacy_status,
                        "selfDeclaredMadeForKids": is_made_for_kids
                    }
                }

                logger.info(f"[YouTubeService] Initializing resumable upload: '{title[:50]}...', Privacy={privacy_status}")
                insert_request = youtube.videos().insert(
                    part="snippet,status",
                    body=body,
                    media_body=MediaFileUpload(
                        video_path,
                        chunksize=1024*1024*5, # 5MB chunks
                        resumable=True,
                        mimetype="video/mp4"
                    )
                )

                upload_response = None
                while upload_response is None:
                    status, upload_response = insert_request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"[YouTubeService] Upload progress: {progress}%")

                new_video_id = upload_response.get("id")
                logger.info(f"✅ [YouTubeService] Upload complete! Video ID: {new_video_id}")

                # Upload thumbnail if available
                if thumbnail_path and os.path.exists(thumbnail_path) and new_video_id:
                    try:
                        logger.info(f"[YouTubeService] Uploading custom thumbnail from {thumbnail_path}...")
                        thumb_media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
                        youtube.thumbnails().set(
                            videoId=new_video_id,
                            media_body=thumb_media
                        ).execute()
                        logger.info(f"✅ [YouTubeService] Custom thumbnail set successfully for {new_video_id}")
                    except Exception as thumb_err:
                        logger.warning(f"⚠️ [YouTubeService] Thumbnail upload warning (non-fatal): {thumb_err}")

                return new_video_id, creds.token

            video_id, updated_token = await asyncio.to_thread(_sync_upload)

            # Persist refreshed token if it was updated
            if channel and updated_token:
                async with AsyncSessionLocal() as session:
                    res = await session.execute(select(Channel).where(Channel.id == channel.id))
                    ch = res.scalar_one_or_none()
                    if ch:
                        ch.access_token_encrypted = encrypt_token(updated_token)
                        ch.is_connected = True
                        await session.commit()

            return {
                "status": "COMPLETED",
                "youtube_video_id": video_id,
                "youtube_url": f"https://youtu.be/{video_id}",
                "privacy": publish_privacy
            }
        except Exception as e:
            logger.error(f"❌ YouTube Data API upload error: {e}")
            raise e

async def publish_video_by_id(video_id: int, target_type: str = "SHORT"):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Video).where(Video.id == video_id))
        video_record = result.scalar_one_or_none()
        if not video_record:
            logger.error(f"Video record {video_id} not found for publishing.")
            return

        res = await YouTubeService.upload_video(
            video_path=video_record.video_path,
            title=video_record.title,
            description=video_record.description,
            tags=video_record.tags or [],
            thumbnail_path=video_record.thumbnail_path,
            publish_mode=video_record.publish_mode
        )

        video_record.youtube_video_id = res.get("youtube_video_id")
        video_record.youtube_url = res.get("youtube_url")
        video_record.status = "COMPLETED"
        await session.commit()
        logger.info(f"Published video {video_id} -> {res.get('youtube_url')}")

youtube_service = YouTubeService()

from typing import Optional
import os
import json
import uuid
import base64
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from backend.config import settings
from backend.db.session import get_db
from backend.db.models import User, Channel, ChannelAutomationProfile, Setting
from backend.api.auth import get_current_user

logger = logging.getLogger(__name__)

# Allow OAuth2 over HTTP for localhost development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

youtube_auth_router = APIRouter(prefix="/api/v1/youtube")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def get_oauth_flow(state: str = None):
    client_config = {
        "web": {
            "client_id": settings.YOUTUBE_CLIENT_ID or "mock_client_id",
            "client_secret": settings.YOUTUBE_CLIENT_SECRET or "mock_client_secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.YOUTUBE_REDIRECT_URI]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=settings.YOUTUBE_REDIRECT_URI,
        autogenerate_code_verifier=False,
        state=state
    )
    return flow

@youtube_auth_router.get("/auth-url")
async def get_auth_url(request: Request, current_user: User = Depends(get_current_user)):
    if not settings.YOUTUBE_CLIENT_ID or not settings.YOUTUBE_CLIENT_SECRET:
        return {
            "status": "UNCONFIGURED",
            "message": "YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET not configured in settings.",
            "auth_url": None
        }

    try:
        origin = request.headers.get("referer") or str(request.base_url)
        origin = origin.rstrip("/")
        if "/channels" in origin:
            origin = origin.split("/channels")[0]
        if "/settings" in origin:
            origin = origin.split("/settings")[0]

        state_data = {"uid": current_user.id, "origin": origin, "rnd": uuid.uuid4().hex[:8]}
        state_str = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
        flow = get_oauth_flow(state=state_str)
        auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
        return {"status": "READY", "auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error generating OAuth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@youtube_auth_router.get("/callback")
async def oauth_callback(request: Request, db: AsyncSession = Depends(get_db)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    target_user_id = 1
    frontend_origin = "https://autotube.co.in"
    if state:
        try:
            decoded = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
            target_user_id = int(decoded.get("uid", 1))
            if decoded.get("origin"):
                frontend_origin = str(decoded.get("origin")).rstrip("/")
        except Exception:
            pass

    try:
        flow = get_oauth_flow(state=state)
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Retrieve channel details from YouTube Data API
        youtube = build("youtube", "v3", credentials=credentials)
        res = youtube.channels().list(mine=True, part="snippet,contentDetails").execute()
        
        channel_id = "unknown"
        channel_title = "Connected YouTube Channel"
        if "items" in res and len(res["items"]) > 0:
            item = res["items"][0]
            channel_id = item.get("id")
            channel_title = item.get("snippet", {}).get("title")

        from backend.services.security import encrypt_token

        enc_token = encrypt_token(credentials.token) if credentials.token else None
        enc_refresh = encrypt_token(credentials.refresh_token) if credentials.refresh_token else None

        # Link channel specifically to target_user_id
        result = await db.execute(select(Channel).where(Channel.user_id == target_user_id))
        user_channel = result.scalar_one_or_none()

        if user_channel:
            user_channel.youtube_channel_id = channel_id
            user_channel.channel_name = channel_title
            user_channel.access_token_encrypted = enc_token or credentials.token
            if enc_refresh or credentials.refresh_token:
                user_channel.refresh_token_encrypted = enc_refresh or credentials.refresh_token
            user_channel.is_connected = True
        else:
            user_channel = Channel(
                user_id=target_user_id,
                youtube_channel_id=channel_id,
                channel_name=channel_title,
                access_token_encrypted=enc_token or credentials.token,
                refresh_token_encrypted=enc_refresh or credentials.refresh_token,
                is_connected=True
            )
            db.add(user_channel)
            await db.flush()

            prof = ChannelAutomationProfile(
                user_id=target_user_id,
                channel_id=user_channel.id,
                niche="Kids Cartoon Stories",
                sub_niche="Hindi Animated Stories",
                language="Hindi",
                visual_mode="IMAGE_MOTION",
                video_format="SHORT",
                videos_per_day=2,
                publish_times=["10:00", "18:00"],
                automation_enabled=True,
                auto_publish=True
            )
            db.add(prof)

        await db.commit()
        logger.info(f"✅ Connected YouTube Channel for user #{target_user_id}: {channel_title} ({channel_id})")
        return RedirectResponse(url=f"{frontend_origin}/channels?youtube_connected=true")

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth verification failed: {e}")

@youtube_auth_router.get("/channel")
async def get_channel_info(
    channel_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Channel).where(Channel.user_id == current_user.id)
    if channel_id:
        query = query.where(Channel.id == channel_id)
    result = await db.execute(query)
    channel = result.scalars().first()
    
    if not channel or not channel.is_connected:
        return {"connected": False, "channel_name": None, "channel_id": None, "has_refresh_token": False}

    has_token = bool(
        channel.access_token_encrypted or 
        channel.refresh_token_encrypted or 
        channel.encrypted_access_token or 
        channel.encrypted_refresh_token
    )
        
    return {
        "connected": bool(channel.is_connected and has_token),
        "channel_name": channel.channel_name,
        "channel_id": getattr(channel, "youtube_channel_id", None) or str(channel.id),
        "has_refresh_token": has_token
    }

@youtube_auth_router.post("/disconnect")
async def disconnect_channel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnects the authenticated user's YouTube channel."""
    result = await db.execute(select(Channel).where(Channel.user_id == current_user.id))
    channels = result.scalars().all()
    for ch in channels:
        ch.is_connected = False
        ch.access_token_encrypted = None
        ch.refresh_token_encrypted = None
        ch.encrypted_access_token = None
        ch.encrypted_refresh_token = None
        ch.youtube_channel_id = None
        ch.channel_name = f"{current_user.username}'s Studio"
    await db.commit()
    logger.info(f"🔌 Channel disconnected for user #{current_user.id}")
    return {"status": "success", "message": "YouTube Channel disconnected successfully."}

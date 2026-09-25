import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from backend.db.session import get_db
from backend.db.models import User, YouTubeChannel, ChannelAutomationProfile
from backend.services.security import hash_password, verify_password, create_access_token, decode_access_token

logger = logging.getLogger(__name__)
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    credential: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str
    plan_tier: str = "FREE_TRIAL"
    credits_balance: float = 50.0

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency: Extract current authenticated user from Bearer header. Enforces multi-tenant isolation."""
    user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            try:
                user_id = int(payload["sub"])
                res = await db.execute(select(User).where(User.id == user_id))
                user = res.scalar_one_or_none()
            except (ValueError, TypeError):
                pass

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to your AutoTube Studio account.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency: Restricts sensitive system configuration endpoints to Admin / Owner accounts only."""
    is_owner = (
        current_user.id == 1 or 
        getattr(current_user, "is_admin", False) or 
        current_user.email in ["monusahani0044@gmail.com", "founder@autotube.ai", "admin@autotube.co.in", "2k24.csai1b.2412184@gmail.com"]
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only the platform owner/admin can modify global system settings & receiver UPI ID."
        )
    return current_user

@auth_router.post("/register", response_model=AuthResponse)
async def register_user(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if username or email exists
    res_user = await db.execute(select(User).where((User.username == req.username) | (User.email == req.email)))
    if res_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or Email already registered.")

    new_user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        credits_balance=50.0,
        plan_tier="FREE_TRIAL"
    )
    db.add(new_user)
    await db.flush()

    # Create initial default channel profile
    new_channel = YouTubeChannel(
        user_id=new_user.id,
        channel_name=f"{req.username}'s Animated Channel",
        description="AutoTube Autonomous Channel",
        is_connected=True
    )
    db.add(new_channel)
    await db.flush()

    new_profile = ChannelAutomationProfile(
        user_id=new_user.id,
        channel_id=new_channel.id,
        niche="Kids Cartoon Stories",
        visual_mode="IMAGE_MOTION",
        videos_per_day=2,
        publish_times=["10:00", "18:00"],
        automation_enabled=True
    )
    db.add(new_profile)
    await db.commit()

    token = create_access_token({"sub": str(new_user.id), "email": new_user.email, "username": new_user.username})
    return AuthResponse(
        access_token=token,
        user_id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        plan_tier=new_user.plan_tier or "FREE_TRIAL",
        credits_balance=new_user.credits_balance if new_user.credits_balance is not None else 50.0
    )

@auth_router.post("/login", response_model=AuthResponse)
async def login_user(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == req.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": str(user.id), "email": user.email, "username": user.username})
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        email=user.email,
        plan_tier=user.plan_tier or "FREE_TRIAL",
        credits_balance=user.credits_balance if user.credits_balance is not None else 50.0
    )

@auth_router.post("/google", response_model=AuthResponse)
async def google_sign_in(req: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate or Register a user via Google OAuth ID Token (One-Tap / Sign-In with Google)."""
    from backend.services.google_auth import verify_google_id_token
    import uuid

    try:
        id_info = await verify_google_id_token(req.credential)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {e}")

    google_email = id_info["email"]
    google_name = id_info.get("name") or google_email.split("@")[0]

    # Look for existing user
    res = await db.execute(select(User).where(User.email == google_email))
    user = res.scalar_one_or_none()

    if not user:
        # Create unique username
        base_uname = "".join(c for c in google_name.lower() if c.isalnum() or c in "_-")[:30]
        if not base_uname:
            base_uname = "user"
        username_candidate = base_uname
        
        # Ensure username uniqueness
        existing_u = await db.execute(select(User).where(User.username == username_candidate))
        if existing_u.scalar_one_or_none():
            username_candidate = f"{base_uname}_{uuid.uuid4().hex[:4]}"

        # Create user with random secure hash (since auth is delegated to Google)
        rand_pass = uuid.uuid4().hex + uuid.uuid4().hex
        user = User(
            username=username_candidate,
            email=google_email,
            password_hash=hash_password(rand_pass),
            credits_balance=50.0,
            plan_tier="FREE_TRIAL",
            subscription_status="ACTIVE"
        )
        db.add(user)
        await db.flush()

        # Provision initial default channel profile
        new_channel = YouTubeChannel(
            user_id=user.id,
            channel_name=f"{google_name}'s Studio",
            description="AutoTube AI Connected Channel",
            is_connected=False
        )
        db.add(new_channel)
        await db.flush()

        new_profile = ChannelAutomationProfile(
            user_id=user.id,
            channel_id=new_channel.id,
            niche="Kids Cartoon Stories",
            visual_mode="IMAGE_MOTION",
            videos_per_day=2,
            publish_times=["10:00", "18:00"],
            automation_enabled=True
        )
        db.add(new_profile)
        await db.commit()
        logger.info(f"[GoogleAuth] Provisioned new user #{user.id} ({user.email}).")
    else:
        logger.info(f"[GoogleAuth] Existing user #{user.id} logged in ({user.email}).")

    token = create_access_token({"sub": str(user.id), "email": user.email, "username": user.username})
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        email=user.email,
        plan_tier=user.plan_tier or "FREE_TRIAL",
        credits_balance=user.credits_balance if user.credits_balance is not None else 50.0
    )

@auth_router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "plan_tier": current_user.plan_tier or "STARTER",
        "subscription_status": current_user.subscription_status or "ACTIVE",
        "credits_balance": current_user.credits_balance,
        "daily_credit_limit": current_user.daily_credit_limit
    }

@auth_router.post("/logout")
async def logout_user():
    return {"message": "Logged out successfully."}

import sys
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import socket
try:
    import anyio._core._sockets
except ImportError:
    anyio = None

# Resilient DNS fallback for Google OAuth endpoints in case local router DNS drops
KNOWN_GOOGLE_HOSTS = {
    "oauth2.googleapis.com": "192.178.158.95",
    "www.googleapis.com": "172.217.118.4",
    "accounts.google.com": "172.217.118.13",
}

_orig_sock_gai = socket.getaddrinfo
def _resilient_sock_gai(host, port, *args, **kwargs):
    try:
        return _orig_sock_gai(host, port, *args, **kwargs)
    except socket.gaierror:
        if host in KNOWN_GOOGLE_HOSTS:
            return _orig_sock_gai(KNOWN_GOOGLE_HOSTS[host], port, *args, **kwargs)
        raise
socket.getaddrinfo = _resilient_sock_gai

if anyio:
    _orig_anyio_gai = anyio._core._sockets.getaddrinfo
    async def _resilient_anyio_gai(host, port, *args, **kwargs):
        try:
            return await _orig_anyio_gai(host, port, *args, **kwargs)
        except Exception:
            if host in KNOWN_GOOGLE_HOSTS:
                return await _orig_anyio_gai(KNOWN_GOOGLE_HOSTS[host], port, *args, **kwargs)
            raise
    anyio._core._sockets.getaddrinfo = _resilient_anyio_gai

from backend.config import settings
from backend.db.init_db import init_db
from backend.api.router import api_router
from backend.api.auth import auth_router
from backend.api.auth_youtube import youtube_auth_router
from backend.api.channels import channels_router
from backend.api.emergency import emergency_router
from backend.api.admin import admin_router
from backend.api.billing import billing_router
from backend.services.job_recovery import job_recovery_service
from backend.tasks.worker import job_queue
from backend.services.scheduler import multi_channel_scheduler

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Initializing AutoTube V1 Multi-Channel SaaS Backend...")
    os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
    await init_db()
    # Recover any crashed or stale jobs from persisted checkpoints
    try:
        await job_recovery_service.recover_stale_jobs()
    except Exception as e:
        logger.warning(f"Error checking stale jobs on startup: {e}")
    # Start dedicated background worker queue
    job_queue.start_worker()
    # Start autonomous multi-channel scheduler loop
    await multi_channel_scheduler.start()
    yield
    print("[INFO] Shutting down AutoTube V1 Backend Engine & Worker Queue...")
    await multi_channel_scheduler.stop()
    await job_queue.stop_worker()

app = FastAPI(
    title="AutoTube V1 — Autonomous Multi-Channel AI YouTube Content SaaS",
    version="1.0.0",
    description="Production-grade AI Video Automation SaaS with Full Animation, Multi-Channel OAuth, and Checkpoint Recovery.",
    lifespan=lifespan
)

from backend.api.rate_limiter import RateLimitMiddleware

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

# Serve storage files statically
os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.STORAGE_LOCAL_DIR), name="storage")

# Include Core REST API routes
app.include_router(api_router)
app.include_router(youtube_auth_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(channels_router, prefix="/api/v1")
app.include_router(emergency_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "product": "AutoTube V1 SaaS",
        "tagline": "Autonomous Multi-Channel AI Video Generation & Distribution Engine",
        "docs_url": "/docs",
        "agent_enabled": settings.AGENT_ENABLED,
        "global_emergency_stop": getattr(settings, "GLOBAL_EMERGENCY_STOP", False)
    }

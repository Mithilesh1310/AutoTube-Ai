import logging
import socket
import httpx
from typing import Optional, Dict, Any
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from backend.config import settings

logger = logging.getLogger(__name__)

# Resilient DNS fallback for Google OAuth endpoints in case local router DNS drops
KNOWN_GOOGLE_HOSTS = {
    "oauth2.googleapis.com": "192.178.158.95",
    "www.googleapis.com": "172.217.118.4",
    "accounts.google.com": "172.217.118.13",
}

_orig_getaddrinfo = socket.getaddrinfo

def _resilient_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)
    except socket.gaierror:
        if host in KNOWN_GOOGLE_HOSTS:
            logger.info(f"[DNS Fallback] Resolving {host} -> {KNOWN_GOOGLE_HOSTS[host]}")
            return _orig_getaddrinfo(KNOWN_GOOGLE_HOSTS[host], port, family, type, proto, flags)
        raise

socket.getaddrinfo = _resilient_getaddrinfo


async def verify_google_id_token(credential: str) -> Dict[str, Any]:
    """
    Verifies a Google OAuth ID Token (JWT) or Access Token (ya29...),
    with automatic resolution, multi-tier fallbacks (native lib, tokeninfo, userinfo).
    Returns dict containing email, name, picture, sub, etc.
    """
    if not credential or not credential.strip():
        raise ValueError("Google credential token is empty.")

    credential = credential.strip()
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "") or settings.YOUTUBE_CLIENT_ID or None

    # Check if this looks like a JWT ID Token (3 parts separated by dots)
    is_jwt = len(credential.split(".")) == 3

    if is_jwt:
        # 1. Try native Google Auth library for JWT
        try:
            req = google_requests.Request()
            id_info = id_token.verify_oauth2_token(
                credential, 
                req, 
                audience=client_id if client_id else None
            )
            email = id_info.get("email")
            if email:
                return {
                    "sub": id_info.get("sub"),
                    "email": email.lower(),
                    "name": id_info.get("name") or email.split("@")[0],
                    "picture": id_info.get("picture", ""),
                    "email_verified": id_info.get("email_verified", True)
                }
        except Exception as e:
            logger.warning(f"[GoogleAuth] Native library verify warning: {e}. Trying tokeninfo endpoint...")

        # 2. Fallback: Google's public tokeninfo endpoint for ID Token
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}")
                if resp.status_code == 200:
                    data = resp.json()
                    email = data.get("email")
                    if email:
                        return {
                            "sub": data.get("sub"),
                            "email": email.lower(),
                            "name": data.get("name") or email.split("@")[0],
                            "picture": data.get("picture", ""),
                            "email_verified": data.get("email_verified") in ["true", True]
                        }
        except Exception as e:
            logger.warning(f"[GoogleAuth] Tokeninfo id_token fallback warning: {e}")

    # 3. Access Token verification via userinfo (for tokens starting with ya29 or non-JWTs)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {credential}"}
            )
            if resp.status_code == 200:
                data = resp.json()
                email = data.get("email")
                if email:
                    return {
                        "sub": data.get("sub"),
                        "email": email.lower(),
                        "name": data.get("name") or email.split("@")[0],
                        "picture": data.get("picture", ""),
                        "email_verified": data.get("email_verified") in ["true", True]
                    }
    except Exception as e:
        logger.warning(f"[GoogleAuth] Userinfo endpoint error: {e}")

    # 4. Access token verification via tokeninfo?access_token=...
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?access_token={credential}")
            if resp.status_code == 200:
                data = resp.json()
                email = data.get("email")
                if email:
                    return {
                        "sub": data.get("sub") or data.get("user_id"),
                        "email": email.lower(),
                        "name": email.split("@")[0],
                        "picture": "",
                        "email_verified": True
                    }
    except Exception as e:
        logger.warning(f"[GoogleAuth] Tokeninfo access_token fallback error: {e}")

    raise ValueError("Invalid Google Token: Could not verify token with Google servers.")

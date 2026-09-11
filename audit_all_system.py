import urllib.request
import urllib.error
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")

endpoints = [
    "/api/v1/health",
    "/api/v1/health/db",
    "/api/v1/dashboard",
    "/api/v1/videos",
    "/api/v1/jobs",
    "/api/v1/characters",
    "/api/v1/analytics",
    "/api/v1/settings",
    "/api/v1/youtube/channel",
    "/api/v1/channels",
    "/api/v1/admin/dashboard",
    "/api/v1/emergency/status"
]

base = "http://127.0.0.1:8000"
results = {}

print("--- AUDITING ALL BACKEND API ENDPOINTS ---")
for ep in endpoints:
    url = base + ep
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SystemAudit/1.0"})
        with urllib.request.urlopen(req, timeout=15) as res:
            raw = res.read().decode("utf-8")
            data = json.loads(raw) if raw.startswith(("{", "[")) else raw
            results[ep] = {"status": res.status, "ok": True}
            print(f"✅ [PASS {res.status}] {ep}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        results[ep] = {"status": e.code, "ok": False, "error": err_body}
        print(f"❌ [FAIL {e.code}] {ep} -> {err_body[:120]}")
    except Exception as e:
        results[ep] = {"status": 0, "ok": False, "error": str(e)}
        print(f"❌ [ERR] {ep} -> {e}")

print("\n--- SUMMARY ---")
passed = sum(1 for r in results.values() if r["ok"])
total = len(results)
print(f"Total: {total} | Passed: {passed} | Failed: {total - passed}")

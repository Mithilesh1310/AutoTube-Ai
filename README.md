# AutoTube V1 — Autonomous Hindi Kids YouTube Content Agent

**AutoTube V1** is an autonomous AI agent system designed to run a Hindi Kids Cartoon YouTube channel with zero or minimal daily human intervention.

It automatically researches, plans, scripts, narrates, generates visuals, edits with FFmpeg (Ken Burns animation & Devanagari subtitles), quality checks, generates thumbnails, uploads to YouTube, and learns from channel performance.

---

## 🚀 Key Features

- **14-Agent LangGraph Pipeline**: Master Orchestrator, Research, Planner, Hindi Script Writer, Script QA (>=80 threshold with retries), Scene Director, Voice Gen, Visual Gen, Video Editor, Video QA, Metadata SEO, Thumbnail, YouTube Upload, and Learning Agent.
- **Daily Content Output**:
  1. **1 Hindi YouTube Short** (9:16 vertical, 1080x1920, 30-60s).
  2. **1 Hindi Cartoon Story Video** (16:9 horizontal, 1920x1080, ~2 min).
- **Persistent Character Universe (Character Bible)**: Pre-seeded characters (*Chintu*, *Momo*, *Titu*, *Mithu*, *Baba Turtle*) with stored visual base prompts, negative prompts, clothing, color palettes, and voice configurations.
- **FFmpeg Ken Burns Video Editor**: Applies camera pan/zoom effects, ducked background music, synchronized character voices, and burnt-in Devanagari Hindi subtitles.
- **Publishing Safety**: Default publishing mode is `UNLISTED`. Global emergency kill switch `AGENT_ENABLED=true/false` supported.
- **Modern Dark AI Dashboard**: Built with Next.js 14, TypeScript, and Tailwind CSS for real-time monitoring of daily missions, video library, analytics, and settings.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy ORM, LangGraph, Pydantic v2, APScheduler.
- **Async Workers**: Celery + Redis + Celery Beat.
- **AI Intelligence**: Official Google Gen AI SDK (`google-genai`) with Gemini models.
- **Voice Provider**: `EdgeTTS` (free high-quality natural Hindi voices), `GoogleTTS`, `ElevenLabs`.
- **Visual Provider**: `KenBurnsVisualProvider` (V1 standard), `Pollinations`, with `VisualProvider` interface for future video APIs (*Veo, Kling, Runway*).
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons.

---

## 📦 Quick Start (Local Development)

### 1. Environment Setup
Copy `.env.example` to `.env` and enter your `GEMINI_API_KEY`:
```bash
cp .env.example .env
```

### 2. Run Backend
```bash
# Initialize DB & Character Bible
python -m backend.db.init_db

# Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```

### 3. Run Frontend
```bash
cd frontend
npm install
npm run dev
```
Access the Dashboard at `http://localhost:3000`.

---

## 🐳 Docker Deployment

Run all backend services, Celery worker/beat, Redis, Postgres, and Next.js frontend with single command:
```bash
docker-compose up --build -d
```

---

## ⏰ Autonomous Daily Schedule (Asia/Kolkata IST)

- **08:00 AM IST**: Generate daily Short and Long video pipeline.
- **10:00 AM IST**: Upload Hindi Short to YouTube.
- **06:00 PM IST**: Upload Hindi Cartoon story video to YouTube.
- **Sunday 11:00 PM IST**: Run Learning Agent weekly channel feedback analysis.

---

## 📜 License
Internal V1 Production System. Proprietary & Confidential.

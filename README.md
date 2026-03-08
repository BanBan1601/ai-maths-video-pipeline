# AI Maths Video Pipeline

Local-first, continuously running AI pipeline for generating 60-second maths short-form videos with Manim animations, academic sourcing, narration, approval gates, and platform publishing.

---

## Prerequisites — install these before cloning

You need the following installed on your machine **before** you clone and run this project.

### 1. Docker Desktop
The entire stack (API, database, workers, frontend) runs in Docker.

- Download: https://www.docker.com/products/docker-desktop
- Windows: requires WSL 2 backend (enabled automatically by the installer)
- After install, open Docker Desktop and wait for the engine to start (whale icon in taskbar)
- Verify: `docker --version` and `docker compose version`

> **Windows disk space note:** Docker Desktop stores its virtual disk on C: by default. Make sure C: has at least **20 GB free** before starting. If C: is tight, move the VHDX to another drive via Docker Desktop → Settings → Resources → Advanced → Disk image location.

### 2. Git
- Download: https://git-scm.com/downloads
- Verify: `git --version`

### 3. Ollama (local LLM — runs natively, not in Docker)
Used for script writing and Manim code generation. Runs on your host machine; the Docker containers reach it via `host.docker.internal`.

- Download: https://ollama.com/download
- After install, pull the required model:
  ```bash
  ollama pull llama3.1:latest
  ```
- Verify: `ollama list` — you should see `llama3.1:latest`
- Ollama must be running when you start the pipeline (it auto-starts on most systems after install)

> A stronger model improves script and Manim quality. `qwen2.5-coder:14b` works well for Manim code generation. Update `OLLAMA_MODEL` in `.env` to switch.

### 4. GitHub CLI (optional — only needed to push to GitHub)
- Download: https://cli.github.com
- Verify: `gh --version`

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/BanBan1601/ai-maths-video-pipeline.git
cd ai-maths-video-pipeline

# 2. Copy environment config
cp .env.example .env

# 3. Create local data directories
mkdir -p data/assets data/renders data/bgm data/previews secrets runs

# 4. Start all services
docker compose up --build -d postgres redis
docker compose up --build -d backend worker beat
docker compose up --build -d frontend

# 5. Open the dashboard
#    http://localhost:3000
#    API docs: http://localhost:8000/docs
```

> On first run, the backend image downloads Python dependencies (~500 MB). Subsequent starts use the cache and are fast.

---

## Services and ports

| Service | URL | Notes |
|---|---|---|
| Dashboard | http://localhost:3000 | React frontend |
| API | http://localhost:8000 | FastAPI |
| API docs | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | Persistent in Docker volume |
| Redis | localhost:6379 | Celery broker |
| Ollama | http://localhost:11434 | Runs natively on host |

---

## How it works

1. Celery beat fires every 2 minutes and calls `seed_video_job` to keep ≥ 3 ideas in the review queue.
2. Each idea is sourced from **Crossref** and **Semantic Scholar** (real academic references).
3. Go to **http://localhost:3000/approvals** to review and approve ideas.
4. After idea approval, a Celery worker calls **Ollama** to generate a 60-second script (5-beat structure).
5. After script approval, Manim code is generated and a layout QA report is produced.
6. After final approval, the video is queued for upload to YouTube / Instagram.

Every stage requires **explicit human approval** — the system never publishes autonomously.

---

## Environment variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | postgres://... | PostgreSQL connection string |
| `REDIS_URL` | redis://redis:6379/0 | Celery broker |
| `OLLAMA_BASE_URL` | http://host.docker.internal:11434 | Ollama endpoint (host machine) |
| `OLLAMA_MODEL` | llama3.1:latest | Model used for generation |
| `LOCAL_ASSET_ROOT` | /data/assets | Where rendered assets are stored |
| `YOUTUBE_CLIENT_SECRETS` | ./secrets/... | Path to YouTube OAuth JSON |
| `INSTAGRAM_APP_ID` | — | Instagram Graph API credentials |

---

## Project structure

```
backend/        FastAPI app, Celery workers, services, models
frontend/       React + Vite dashboard
infra/          Manim base templates
docs/           Architecture notes and build roadmap
scripts/        Bootstrap and start helpers
docker-compose.yml
```

---

## Core principles

1. **Autonomous generation** — the scheduler keeps proposing videos while the service runs.
2. **Human approval gates** — nothing crosses idea, script, render, or upload stages without your sign-off.
3. **Source-grounded content** — every claim is attached to peer-reviewed papers or trusted textbooks via Crossref and Semantic Scholar.
4. **Deterministic layout QA** — overlap detection, caption-safe zones, font size, edge padding.
5. **Local-first** — no cloud services required to run; Ollama and all workers run on your machine.

---

## Stopping and restarting

```bash
# Stop all containers (keeps data)
docker compose down

# Stop and wipe the database (fresh start)
docker compose down -v

# Restart after a reboot
docker compose up -d
```

Ollama persists its models locally and does not need to be re-downloaded after reboot.

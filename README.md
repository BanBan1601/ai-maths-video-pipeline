# AI Maths Video Pipeline

Local-first, continuously running AI pipeline for generating 1-minute maths shorts/reels with Manim, narration, background music, academic sourcing, approval gates, and platform publishing.

## What this scaffold includes

- `backend/`: FastAPI API, orchestration contracts, data models, worker stubs, QA logic
- `frontend/`: React dashboard skeleton for queue visibility, approvals, and preview
- `infra/`: Manim template assets and deployment notes
- `docs/`: architecture, build phases, and implementation notes
- `scripts/`: local bootstrap and dependency installation helpers
- `docker-compose.yml`: local-first dev stack

## Core principles

1. **Autonomous generation**: the scheduler keeps creating candidate videos while the service is running.
2. **Human approval gates**: no item crosses idea, script, final render, or upload phases without explicit approval.
3. **Source-grounded content**: every nontrivial claim must be attached to trusted academic references.
4. **Deterministic QA**: the system validates spacing, overlap, subtitle-safe regions, and render consistency.
5. **Parallelism**: multiple videos can be in different stages at the same time.
6. **Local-first**: runs on your machine via Docker Compose; all critical services are self-hostable.

## Suggested development order

1. Bring up infrastructure with Docker Compose.
2. Implement DB migrations and seed a default project.
3. Build the idea → script → render → upload state machine.
4. Add source-grounding and citation checks.
5. Add Manim static and screenshot-based QA.
6. Add narration and composition.
7. Add dashboard review and approvals.
8. Add YouTube/Instagram publishing adapters.

## Quick start

```bash
cp .env.example .env
./scripts/bootstrap.sh

docker compose up --build
```

Backend: `http://localhost:8000`
Frontend: `http://localhost:3000`

## Important operational note

Instagram publishing should be treated as **capability-dependent**. The pipeline must check whether the connected account supports API publishing before offering automatic upload; otherwise it should stop at an upload-ready state and show the reason in the dashboard.

# Build Roadmap

## Phase 1 — Foundation
- Stand up Docker Compose stack.
- Add SQLAlchemy models, Alembic, and project seed data.
- Implement project, video job, approval, and asset entities.
- Add dashboard with queue + item detail views.

## Phase 2 — Orchestration
- Build finite state machine for `idea_pending -> idea_approved -> script_pending -> ... -> upload_completed`.
- Add Celery routing and idempotent job execution.
- Add concurrency controls per project and per resource-heavy stage.

## Phase 3 — Research + Scripting
- Implement topic generator, source retriever, claim linker, and script writer.
- Add trust scoring and mandatory citation coverage.
- Prevent progression if script claims lack evidence.

## Phase 4 — Manim Generation
- Introduce strict scene schema.
- Implement reusable visual blocks and safe layout helpers.
- Render with deterministic settings and store screenshots + metrics.

## Phase 5 — QA + Repair
- Bounding-box overlap checks.
- Subtitle-safe region checks.
- Screenshot-based cramped-layout detection.
- Automatic layout repair loop with capped retries.

## Phase 6 — Audio + Composition
- Add offline TTS.
- Normalize loudness, duck BGM, align subtitles.
- Compose vertical 9:16 videos suitable for Shorts/Reels.

## Phase 7 — Publishing
- Add YouTube upload adapter.
- Add Instagram capability checker and reel publishing adapter.
- Surface per-platform readiness and errors in dashboard.

## Phase 8 — Observability
- Add structured logs, run history, retry traces, asset lineage.
- Add dashboard metrics and worker activity feed.

# Repository Map

## backend/
- `app/main.py`: FastAPI entrypoint
- `app/api/routes.py`: HTTP endpoints for dashboard actions
- `app/core/config.py`: environment and settings
- `app/db/session.py`: SQLAlchemy engine and session factory
- `app/models/`: persistent entities
- `app/schemas/`: API payloads
- `app/services/`: domain logic
- `app/workers/`: Celery app and tasks

## frontend/
- `src/pages/DashboardPage.jsx`: top-level dashboard UI
- `src/components/StageCard.jsx`: stage metrics card
- `src/components/ApprovalPanel.jsx`: review actions panel

## docs/
- `build_roadmap.md`: phased implementation plan
- `state_machine.md`: pipeline lifecycle model
- `repository_map.md`: file-level orientation

## scripts/
- `bootstrap.sh`: local directory and prerequisite setup

## infra/
- `manim_templates/short_base.py`: base vertical short template

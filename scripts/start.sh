#!/usr/bin/env bash
# Quick-start script for the AI Maths Video Pipeline
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Checking prerequisites..."
for cmd in docker docker-compose; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is required. Install Docker Desktop first."
    exit 1
  fi
done

echo "==> Creating local directories..."
mkdir -p "$ROOT/data/assets" "$ROOT/data/renders" "$ROOT/data/bgm" \
         "$ROOT/data/previews" "$ROOT/secrets" "$ROOT/runs"

echo "==> Setting up .env..."
if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "  Created .env from .env.example — edit it if needed."
fi

echo "==> Starting services..."
cd "$ROOT"
docker compose up --build -d

echo ""
echo "==> Services starting. Check status with: docker compose ps"
echo ""
echo "  Dashboard: http://localhost:3000"
echo "  API docs:  http://localhost:8000/docs"
echo "  Ollama:    http://localhost:11434"
echo ""
echo "==> Pull a model into Ollama (run once after first boot):"
echo "  docker compose exec ollama ollama pull llama3.1:8b"
echo ""
echo "==> To follow logs:"
echo "  docker compose logs -f backend worker"

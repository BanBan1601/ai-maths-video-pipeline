#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT_DIR/data/assets" "$ROOT_DIR/data/renders" "$ROOT_DIR/data/bgm" "$ROOT_DIR/data/previews" "$ROOT_DIR/secrets"

echo "Preparing local directories..."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Desktop or Docker Engine first."
  exit 1
fi

echo "Directory bootstrap complete."
echo "Next: copy .env.example to .env and run docker compose up --build"

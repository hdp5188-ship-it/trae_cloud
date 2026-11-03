#!/usr/bin/env bash
# Start the render API. Env file defaults to /etc/blender-render.env.
set -euo pipefail

ENV_FILE="${ENV_FILE:-/etc/blender-render.env}"
VENV_DIR="${VENV_DIR:-/opt/blender-render-venv}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

cd "$HERE"
exec "${VENV_DIR}/bin/uvicorn" app:app --host 0.0.0.0 --port "${PORT:-8000}"

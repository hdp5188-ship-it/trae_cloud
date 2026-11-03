#!/usr/bin/env bash
# Install Blender + render service on a fresh Ubuntu 22.04 GPU box (AutoDL / generic cloud).
set -euo pipefail

BLENDER_VERSION="${BLENDER_VERSION:-4.2.3}"
INSTALL_DIR="${INSTALL_DIR:-/opt}"
VENV_DIR="${VENV_DIR:-/opt/blender-render-venv}"
APP_DIR="${APP_DIR:-/opt/blender-render}"
RENDER_ROOT="${RENDER_ROOT:-/data}"
ENV_FILE="${ENV_FILE:-/etc/blender-render.env}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  SUDO="sudo"
fi

echo "==> installing system dependencies"
$SUDO apt-get update
$SUDO apt-get install -y --no-install-recommends \
  python3 python3-pip python3-venv ffmpeg curl ca-certificates xz-utils \
  libxi6 libxrender1 libxkbcommon0 libsm6 libgl1 libxxf86vm1 \
  libxfixes3 libxinerama1 libxcursor1 libxrandr2

if ! command -v blender >/dev/null 2>&1; then
  echo "==> downloading Blender ${BLENDER_VERSION}"
  curl -fsSL \
    "https://download.blender.org/release/Blender4.2/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    -o /tmp/blender.tar.xz
  $SUDO tar -xJf /tmp/blender.tar.xz -C "$INSTALL_DIR"
  $SUDO ln -sf "${INSTALL_DIR}/blender-${BLENDER_VERSION}-linux-x64/blender" /usr/local/bin/blender
  rm -f /tmp/blender.tar.xz
fi

echo "==> creating Python environment"
$SUDO python3 -m venv "$VENV_DIR"
$SUDO "$VENV_DIR/bin/pip" install --no-cache-dir -r "${HERE}/requirements.txt"

$SUDO mkdir -p "$RENDER_ROOT"
if [ ! -f "$ENV_FILE" ]; then
  TOKEN="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  $SUDO tee "$ENV_FILE" >/dev/null <<EOF
RENDER_TOKEN=${TOKEN}
RENDER_ROOT=${RENDER_ROOT}
BLENDER_BIN=/usr/local/bin/blender
FFMPEG_BIN=/usr/bin/ffmpeg
RENDER_DEVICE=auto
PORT=8000
MAX_UPLOAD_MB=4096
MAX_RENDER_MINUTES=240
EOF
  echo "==> token generated (store it): ${TOKEN}"
else
  echo "==> keeping existing ${ENV_FILE}"
fi

$SUDO mkdir -p "$APP_DIR"
$SUDO cp "${HERE}/app.py" "${HERE}/render.py" "${HERE}/requirements.txt" "${HERE}/start.sh" "$APP_DIR/"
$SUDO chmod +x "${APP_DIR}/start.sh"

echo
echo "Installed. Start the service with:"
echo "  sudo env ENV_FILE=${ENV_FILE} ${APP_DIR}/start.sh"
echo "Then check:  curl http://127.0.0.1:8000/health"

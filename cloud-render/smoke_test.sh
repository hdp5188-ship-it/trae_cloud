#!/usr/bin/env bash
# End-to-end check: build a test scene, submit, poll, download MP4.
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8000}"
TOKEN="${RENDER_TOKEN:?export RENDER_TOKEN first}"
BLENDER="${BLENDER_BIN:-blender}"
FRAMES="${FRAMES:-24}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "==> building test scene"
"$BLENDER" --disable-autoexec -b -P "${HERE}/make_test_scene.py" -- \
  --out "$TMP/test.blend" --frames "$FRAMES"

echo "==> submitting job"
RESP="$(curl -fsS -X POST "$BASE/jobs" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@${TMP}/test.blend" \
  -F fps=12 -F start=1 -F end="$FRAMES" \
  -F width=640 -F height=360 -F samples=16)"
JOB="$(printf '%s' "$RESP" | python3 -c 'import json,sys; print(json.load(sys.stdin)["job_id"])')"
echo "job: $JOB"

STATUS=""
for _ in $(seq 1 120); do
  STATUS="$(curl -fsS -H "Authorization: Bearer ${TOKEN}" "$BASE/jobs/$JOB")"
  printf '%s' "$STATUS" | python3 -c \
    'import json,sys; j=json.load(sys.stdin); print(j["status"], j["stage"], str(j["progress"])+"%", j.get("error") or "")'
  STATE="$(printf '%s' "$STATUS" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [ "$STATE" = "done" ] && break
  [ "$STATE" = "failed" ] && { echo "render failed"; exit 1; }
  sleep 3
done

[ "$STATE" = "done" ] || { echo "timed out"; exit 1; }

echo "==> downloading video"
curl -fsS -H "Authorization: Bearer ${TOKEN}" "$BASE/jobs/$JOB/video" -o "${HERE}/smoke-out.mp4"
ls -lh "${HERE}/smoke-out.mp4"
echo "done: ${HERE}/smoke-out.mp4"

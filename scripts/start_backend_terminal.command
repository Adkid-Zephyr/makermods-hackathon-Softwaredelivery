#!/bin/zsh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LEROBOT_ROOT="/Users/adkid/Documents/Makermods_Hackathon/lerobot-MakerMods-main"
PYTHON_BIN="$LEROBOT_ROOT/.conda-env/bin/python"
LOG_DIR="$REPO_ROOT/outputs"
LOG_FILE="$LOG_DIR/backend-terminal.log"

mkdir -p "$LOG_DIR"
cd "$REPO_ROOT"

unset __CFBundleIdentifier

echo "Requesting Camera permission from Terminal.app..."
if ! swift "$REPO_ROOT/scripts/request_camera_access.swift"; then
  echo
  echo "Camera permission is still not authorized."
  echo "If macOS showed a prompt, allow Terminal to access the camera and rerun this script."
  echo "If no prompt appeared, run 'tccutil reset Camera' in Terminal and rerun."
  exec zsh -i
fi

echo
echo "Starting backend from Terminal..."
echo "Log file: $LOG_FILE"
echo "Keep this Terminal window open while using the UI."

PYTHONPATH="$REPO_ROOT:$LEROBOT_ROOT/src" \
  "$PYTHON_BIN" -u -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --log-level info \
  2>&1 | tee "$LOG_FILE"

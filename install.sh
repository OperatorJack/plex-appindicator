#!/usr/bin/env bash
set -euo pipefail

# Resolve repo directory (directory containing this script)
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

SCRIPT_PATH="$REPO_DIR/plex-appindicator.py"
SERVICE_TEMPLATE="$REPO_DIR/plex-watcher.service"

SYSTEMD_DIR="$HOME/.config/systemd/user"
SYSTEMD_SERVICE="$SYSTEMD_DIR/plex-watcher.service"

BASE_SVG_SRC="$REPO_DIR/plex-base.svg"
BASE_SVG_DEST="$HOME/.local/share/icons/plex/plex-base.svg"

echo "Repo directory:        $REPO_DIR"
echo "Script path:           $SCRIPT_PATH"
echo "Service template:      $SERVICE_TEMPLATE"
echo "Systemd service dest:  $SYSTEMD_SERVICE"
echo "Base SVG src:          $BASE_SVG_SRC"
echo "Base SVG dest:         $BASE_SVG_DEST"
echo

# 1) Ensure script exists
if [[ ! -f "$SCRIPT_PATH" ]]; then
  echo "ERROR: $SCRIPT_PATH not found."
  exit 1
fi

# 2) Ensure base SVG exists and copy it to the expected location
if [[ ! -f "$BASE_SVG_SRC" ]]; then
  echo "ERROR: $BASE_SVG_SRC not found."
  exit 1
fi

mkdir -p "$(dirname "$BASE_SVG_DEST")"
cp "$BASE_SVG_SRC" "$BASE_SVG_DEST"
echo "Copied plex-base.svg to $BASE_SVG_DEST"

# 3) Make the script executable
chmod +x "$SCRIPT_PATH"
echo "Marked $SCRIPT_PATH as executable"

# 4) Generate the user systemd unit from the template, with absolute ExecStart
mkdir -p "$SYSTEMD_DIR"

if [[ ! -f "$SERVICE_TEMPLATE" ]]; then
  echo "ERROR: $SERVICE_TEMPLATE not found."
  exit 1
fi

# Replace __EXEC_START__ with the absolute script path
sed "s|__EXEC_START__|$SCRIPT_PATH|" "$SERVICE_TEMPLATE" > "$SYSTEMD_SERVICE"
echo "Wrote systemd unit to $SYSTEMD_SERVICE"

# 5) Reload systemd user units and enable the service
systemctl --user daemon-reload
systemctl --user enable --now plex-watcher.service

echo
echo "Installation complete."
echo "The Plex AppIndicator service is now running as a user service."
echo "You can check status with:"
echo "  systemctl --user status plex-watcher.service"

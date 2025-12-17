#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="plex-watcher.service"

# Check if the service is installed
if ! systemctl --user list-unit-files "$SERVICE_NAME" &>/dev/null; then
  echo "ERROR: $SERVICE_NAME is not installed."
  echo "Run ./install.sh first."
  exit 1
fi

# Reload systemd in case the service file changed
systemctl --user daemon-reload

# Restart the service
echo "Restarting $SERVICE_NAME..."
systemctl --user restart "$SERVICE_NAME"

echo "Done. Service status:"
systemctl --user status "$SERVICE_NAME" --no-pager


#!/bin/bash

SERVICE_NAME="gemini-api"
SERVICE_FILE="${SERVICE_NAME}.service"
INSTALL_DIR=$(pwd)
CURRENT_USER=$(whoami)
SYSTEMD_DIR="/etc/systemd/system"

echo "--- Installing Gemini API Service ---"
echo "Detected User: $CURRENT_USER"
echo "Detected Path: $INSTALL_DIR"

# 1. Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: $SERVICE_FILE not found in $INSTALL_DIR"
    exit 1
fi

# 2. Update placeholders in the service file
sed "s|{{WORKDIR}}|${INSTALL_DIR}|g; s|{{USER}}|${CURRENT_USER}|g" "$SERVICE_FILE" > "${SERVICE_FILE}.tmp"

# 3. Copy to systemd
echo "Copying service file to $SYSTEMD_DIR..."
sudo cp "${SERVICE_FILE}.tmp" "${SYSTEMD_DIR}/${SERVICE_FILE}"
rm "${SERVICE_FILE}.tmp"

# 4. Reload and Start
echo "Reloading systemd and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

echo "--- Installation Complete ---"
sudo systemctl status "$SERVICE_NAME" --no-pager
echo "Tip: Use 'sudo journalctl -u $SERVICE_NAME -f' to see live logs."

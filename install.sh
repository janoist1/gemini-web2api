#!/bin/bash

# Gemini API Service Installer for Raspberry Pi

SERVICE_NAME="gemini-api"
SERVICE_FILE="${SERVICE_NAME}.service"
INSTALL_DIR=$(pwd)
SYSTEMD_DIR="/etc/systemd/system"

echo "--- Installing Gemini API Service ---"

# 1. Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: $SERVICE_FILE not found in $INSTALL_DIR"
    exit 1
fi

# 2. Update the WorkingDirectory and ExecStart in the service file to match current path
# We use a temporary file to avoid corrupting the original
sed "s|WorkingDirectory=.*|WorkingDirectory=${INSTALL_DIR}|" "$SERVICE_FILE" > "${SERVICE_FILE}.tmp"
sed -i "s|ExecStart=.*|ExecStart=${INSTALL_DIR}/.venv/bin/python gemini.py server|" "${SERVICE_FILE}.tmp"

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

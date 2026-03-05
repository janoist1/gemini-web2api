#!/bin/bash

# Gemini API Service Uninstaller for Raspberry Pi

SERVICE_NAME="gemini-api"
SERVICE_FILE="${SERVICE_NAME}.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "--- Uninstalling Gemini API Service ---"

# 1. Stop and Disable
echo "Stopping and disabling service..."
sudo systemctl stop "$SERVICE_NAME"
sudo systemctl disable "$SERVICE_NAME"

# 2. Remove files
if [ -f "${SYSTEMD_DIR}/${SERVICE_FILE}" ]; then
    echo "Removing service file from $SYSTEMD_DIR..."
    sudo rm "${SYSTEMD_DIR}/${SERVICE_FILE}"
fi

# 3. Reload
echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "--- Uninstallation Complete ---"

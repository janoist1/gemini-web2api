# Gemini Web2API Proxy for Raspberry Pi

This project provides an OpenAI-compatible API proxy for Google Gemini, specifically optimized to run on headless systems like a Raspberry Pi without triggering macOS Keychain prompts or requiring a GUI.

## Features

- **OpenAI Compatible**: Use Gemini as a drop-in replacement for OpenAI API endpoints (`/v1/chat/completions`, `/v1/models`).
- **Dynamic Model Selection**: Supports `gemini-3.0-pro`, `gemini-3.0-flash`, and `gemini-3.0-flash-thinking`.
- **Raspberry Pi OS Lite Support**: Headless implementation without GUI dependencies.
- **Keychain Blocking**: Uses a low-level monkey-patch to prevent accidental browser/Keychain access.
- **Auto-Refresh**: Automatically maintains its own session cookies through a background rotation task.
- **Simple Deployment**: Includes install/uninstall scripts for Linux services.

## Setup

1.  **Extract Cookies (on Mac/PC)**:
    Run the update script to get your browser cookies into the `.env` file:
    ```bash
    ./gemini.py update
    ```
2.  **Deploy to Raspberry Pi**:
    Clone the repo (including submodules) and copy your `.env` file to the same directory on the Pi:
    ```bash
    git clone --recursive https://github.com/janoist1/gemini-web2api.git
    cd gemini-web2api
    ```
3.  **Install as a Service**:
    The installer handles venv creation, requirements, and systemd setup:
    ```bash
    chmod +x install.sh
    ./install.sh
    ```

## Maintenance & Updates

### How to update the project
To pull the latest changes from this proxy and the underlying Gemini library:
```bash
git pull origin main
git submodule update --remote --merge
./install.sh
```

### Managing the Service
- **Check Status**: `sudo systemctl status gemini-api`
- **Restart**: `sudo systemctl restart gemini-api`
- **View Logs**: `sudo journalctl -u gemini-api -f`
- **Uninstall**: `./uninstall.sh`

## Credits

This project uses [gemini-webapi](https://github.com/HanaokaYuzu/Git-API) as a core engine, managed via Git submodules.

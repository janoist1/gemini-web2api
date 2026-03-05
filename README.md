# Gemini Web2API Proxy for Raspberry Pi

This project provides an OpenAI-compatible API proxy for Google Gemini, specifically optimized to run on headless systems like a Raspberry Pi without triggering macOS Keychain prompts or requiring a GUI.

## Features

- **OpenAI Compatible**: Use Gemini as a drop-in replacement for OpenAI API endpoints.
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
    Clone the repo and copy your `.env` file to the same directory on the Pi.
3.  **Install as a Service**:
    ```bash
    chmod +x install.sh
    ./install.sh
    ```

## Usage

The server runs on port `8000` by default. You can point your LLM clients to `http://<your-pi-ip>:8000/v1`.

## Credits

This project includes a local copy of [gemini-webapi](https://github.com/vual/gemini-webapi) for easier management and patching.

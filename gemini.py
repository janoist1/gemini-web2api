#!/usr/bin/env python3
import sys
import os
import subprocess
import argparse

def run_command(cmd_list):
    try:
        # Use python from .venv if available
        venv_python = os.path.join(os.getcwd(), ".venv", "bin", "python")
        python_exe = venv_python if os.path.exists(venv_python) else sys.executable
        
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.join(os.getcwd(), "gemini_api_lib", "src") + (":" + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
        
        full_cmd = [python_exe] + cmd_list
        subprocess.run(full_cmd, env=env)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Gemini Web2API CLI Controller")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: update
    update_parser = subparsers.add_parser("update", help="Update cookies from Chrome and save to .env")
    
    # Command: server
    server_parser = subparsers.add_parser("server", help="Start the Gemini API Proxy server")
    server_parser.add_argument("--port", "-p", type=int, help="Override server port")

    # Command: ask
    ask_parser = subparsers.add_parser("ask", help="Query the Gemini model via CLI")
    ask_parser.add_argument("prompt", nargs="*", help="The message to send")
    ask_parser.add_argument("--model", "-m", help="Specify model name")

    # Command: test
    test_parser = subparsers.add_parser("test", help="Run a quick test of the Gemini client library")

    args = parser.parse_args()

    if args.command == "update":
        print("--- Updating Gemini Cookies ---")
        run_command(["update_cookies.py"])

    elif args.command == "server":
        print("--- Starting Server ---")
        env = os.environ.copy()
        if args.port:
            env["PORT"] = str(args.port)
        run_command(["server.py"])

    elif args.command == "ask":
        # Pass through arguments to ask_client.py
        cmd = ["ask_client.py"]
        if args.prompt:
            cmd.extend(args.prompt)
        if args.model:
            cmd.extend(["--model", args.model])
        run_command(cmd)

    elif args.command == "test":
        print("--- Running Library Test ---")
        run_command(["test_gemini.py"])

    else:
        parser.print_help()

if __name__ == "__main__":
    main()

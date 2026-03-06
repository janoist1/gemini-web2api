import json
import os

config_path = os.path.expanduser("~/.openclaw/openclaw.json")
agent_models_path = os.path.expanduser("~/.openclaw/agents/main/agent/models.json")

def update_config(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Update providers
    providers = data.get("models", {}).get("providers", {})
    provider = providers.get("custom-127-0-0-1-8000")
    if provider:
        provider["api"] = "openai-chat"
        # Add Pro model if not present
        model_ids = [m["id"] for m in provider["models"]]
        if "gemini-3.0-pro" not in model_ids:
            provider["models"].append({
                "id": "gemini-3.0-pro",
                "name": "gemini-3.0-pro (Custom Provider)",
                "reasoning": True,
                "input": ["text"],
                "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                "contextWindow": 128000,
                "maxTokens": 8192,
                "api": "openai-chat"
            })
    
    # Update default agent model
    agents = data.get("agents", {})
    if agents:
        defaults = agents.get("defaults", {})
        if defaults:
            defaults["model"] = {"primary": "custom-127-0-0-1-8000/gemini-3.0-pro"}
            # Ensure the specific model config exists
            if "models" not in defaults:
                defaults["models"] = {}
            defaults["models"]["custom-127-0-0-1-8000/gemini-3.0-pro"] = {}

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Updated: {path}")

def update_agent_models(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, 'r') as f:
        data = json.load(f)
    
    providers = data.get("providers", {})
    provider = providers.get("custom-127-0-0-1-8000")
    if provider:
        provider["api"] = "openai-chat"
        model_ids = [m["id"] for m in provider["models"]]
        if "gemini-3.0-pro" not in model_ids:
            provider["models"].append({
                "id": "gemini-3.0-pro",
                "name": "gemini-3.0-pro (Custom Provider)",
                "reasoning": True,
                "input": ["text"],
                "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                "contextWindow": 128000,
                "maxTokens": 8192,
                "api": "openai-chat"
            })

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Updated: {path}")

update_config(config_path)
update_agent_models(agent_models_path)

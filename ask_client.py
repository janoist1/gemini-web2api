import argparse
import asyncio
import sys
import httpx

# Default configuration
DEFAULT_MODEL = "gemini-3.0-pro"
API_URL = "http://localhost:8000/v1/chat/completions"

async def main():
    parser = argparse.ArgumentParser(description="Query the local Gemini API.")
    parser.add_argument("prompt", nargs="*", help="The prompt to send to the API. If empty, reads from stdin.")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help=f"The model to use (default: {DEFAULT_MODEL})")
    
    args = parser.parse_args()

    # Determine prompt
    if args.prompt:
        prompt_text = " ".join(args.prompt)
    else:
        # Check if there is data in stdin
        if not sys.stdin.isatty():
            prompt_text = sys.stdin.read().strip()
        else:
            print("Error: Please provide a prompt as an argument or via stdin.")
            sys.exit(1)

    if not prompt_text:
        print("Error: Empty prompt.")
        sys.exit(1)

    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt_text}]
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(API_URL, json=payload)
            response.raise_for_status()
            
            data = response.json()
            # Extract content from OpenAI format
            content = data["choices"][0]["message"]["content"]
            print(content)
            
    except httpx.HTTPError as e:
        print(f"Error communicating with API: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

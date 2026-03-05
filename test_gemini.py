import asyncio
import os
from dotenv import load_dotenv
from gemini_webapi import GeminiClient

load_dotenv()

SECURE_1PSID = os.getenv("GEMINI_SECURE_1PSID")
SECURE_1PSIDTS = os.getenv("GEMINI_SECURE_1PSIDTS")


async def main():
    if not SECURE_1PSID or not SECURE_1PSIDTS:
        print("Error: Gemini cookies not found in environment.")
        print("Please run 'python update_cookies.py' to extract cookies from Chrome and update your .env file.")
        return
        
    print("Initializing client...")
    client = GeminiClient(SECURE_1PSID, SECURE_1PSIDTS, proxy=None)
    await client.init(timeout=120, auto_close=False, close_delay=300, auto_refresh=True)
    print("Client initialized.")

    print("Starting chat...")
    chat = client.start_chat()
    print("Sending message...")
    response = await chat.send_message("Hello, this is a test.")
    print(f"Response: {response.text}")


if __name__ == "__main__":
    asyncio.run(main())

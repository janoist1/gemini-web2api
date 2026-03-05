import os
import browser_cookie3
from dotenv import load_dotenv, set_key

def update_cookies():
    # Load existing .env if it exists
    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("")
    
    load_dotenv(env_path)
    
    print("Extracting cookies from Chrome...")
    try:
        # Get cookies specifically for google.com
        cj = browser_cookie3.chrome(domain_name=".google.com")
        
        secure_1psid = None
        secure_1psidts = None
        secure_1psidcc = None
        
        for cookie in cj:
            if cookie.name == "__Secure-1PSID":
                secure_1psid = cookie.value
            elif cookie.name == "__Secure-1PSIDTS":
                secure_1psidts = cookie.value
            elif cookie.name == "__Secure-1PSIDCC":
                secure_1psidcc = cookie.value
        
        if not secure_1psid or not secure_1psidts:
            print("Error: Could not find required cookies (__Secure-1PSID or __Secure-1PSIDTS).")
            print("Make sure you are logged into Gemini (https://gemini.google.com) in Chrome.")
            return

        # Update .env file
        set_key(env_path, "GEMINI_SECURE_1PSID", secure_1psid)
        set_key(env_path, "GEMINI_SECURE_1PSIDTS", secure_1psidts)
        if secure_1psidcc:
            set_key(env_path, "GEMINI_SECURE_1PSIDCC", secure_1psidcc)
            print(f"GEMINI_SECURE_1PSIDCC: {secure_1psidcc[:10]}...{secure_1psidcc[-10:]}")
        
        print("Successfully updated .env file with new cookies.")
        print(f"GEMINI_SECURE_1PSID: {secure_1psid[:10]}...{secure_1psid[-10:]}")
        print(f"GEMINI_SECURE_1PSIDTS: {secure_1psidts[:10]}...{secure_1psidts[-10:]}")

    except Exception as e:
        print(f"Error extracting cookies: {e}")
        print("Tip: If on macOS, Chrome might need to be closed or you might need to grant Full Disk Access to your terminal.")

if __name__ == "__main__":
    update_cookies()

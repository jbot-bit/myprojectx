import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("PROJECTX_BASE_URL", "").strip()
user = os.getenv("PROJECTX_USERNAME", "").strip()
key = os.getenv("PROJECTX_API_KEY", "").strip()
live = os.getenv("PROJECTX_LIVE", "false").lower() in ("1", "true", "yes", "y")


def headers(token=None):
    h = {"accept": "text/plain", "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


with httpx.Client(timeout=30.0) as c:
    # Login
    r = c.post(f"{base_url}/api/Auth/loginKey", headers=headers(), json={"userName": user, "apiKey": key})
    r.raise_for_status()
    tok = r.json()["token"]

    # Search MGC contracts
    print("=== MGC Contract Search ===")
    r = c.post(f"{base_url}/api/Contract/search", headers=headers(tok), json={"searchText": "MGC", "live": live})
    r.raise_for_status()
    search_data = r.json()
    print(json.dumps(search_data, indent=2))

    # List all available contracts
    print("\n=== All Available Contracts ===")
    r = c.post(f"{base_url}/api/Contract/available", headers=headers(tok), json={"live": live})
    r.raise_for_status()
    available_data = r.json()
    print(json.dumps(available_data, indent=2))

# substack_api/publish_by_id.py

import sys
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": os.getenv("PUBLICATION_URL"),
    "Content-Type": "application/json"
})

cookie_map = {
    "sid": os.getenv("SID"),
    "substack.lli": os.getenv("SUBSTACK_LLI"),
    "substack.sid": os.getenv("SUBSTACK_SID")
}
for k, v in cookie_map.items():
    if v:
        session.cookies.set(k, v, domain=".substack.com")

def publish_draft_by_id(draft_id: str):
    """
    Publish a draft when we already know its ID.
    This hits the internal post endpoint directly (no listing).
    """
    url = f"https://substack.com/api/v1/post/{draft_id}/publish"

    resp = session.post(url, data=json.dumps({}))
    if resp.status_code != 200:
        print("Error publishing draft:", resp.status_code, resp.text)
        sys.exit(1)

    print(f"Draft {draft_id} published successfully.")
    return resp.json()

def main():
    if len(sys.argv) < 2:
        print("Usage: python publish_by_id.py <draft_id>")
        sys.exit(1)

    draft_id = sys.argv[1].strip()
    print(f"=== SUBSTACK PUBLISH BY ID ===")
    publish_draft_by_id(draft_id)

if __name__ == "__main__":
    main()

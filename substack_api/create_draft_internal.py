# substack_api/create_draft_internal.py

import sys
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Referer": os.getenv("PUBLICATION_URL"),
    "Content-Type": "application/json"
})

cookie_map = {
    "sid": os.getenv("SID"),
    "substack.lli": os.getenv("SUBSTACK_LILI"),
    "substack.sid": os.getenv("SUBSTACK_SID")
}
for k, v in cookie_map.items():
    if v:
        session.cookies.set(k, v, domain=".substack.com")

def create_draft(markup_json):
    url = "https://substack.com/api/v1/post"

    payload = {
        "type": "draft",
        "body": markup_json,
        "title": None,
        "subtitle": None,
        "is_published": False
    }

    resp = session.post(url, data=json.dumps(payload))
    if resp.status_code != 200:
        print("Error creating draft:", resp.status_code, resp.text)
        return None

    return resp.json()

def main():
    if len(sys.argv) < 2:
        print("Usage: python create_draft_internal.py <markup_file>")
        sys.exit(1)

    markup_file = sys.argv[1]

    with open(markup_file, "r", encoding="utf-8") as f:
        markup_json = json.loads(f.read())

    draft = create_draft(markup_json)

    if not draft:
        print("Draft creation failed.")
        sys.exit(1)

    draft_id = draft.get("id")
    print(f"Draft created with ID: {draft_id}")

    with open("draft_id.txt", "w") as f:
        f.write(str(draft_id))

if __name__ == "__main__":
    main()

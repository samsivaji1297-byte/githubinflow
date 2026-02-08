# substack_api/publish_latest_draft.py

import sys
from draft_publish import publish_draft, get_drafts, build_headers

if __name__ == "__main__":
    print("=== SUBSTACK AUTO-PUBLISH ===")

    drafts = get_drafts()

    if not drafts:
        print("No drafts found. Cannot publish.")
        sys.exit(1)

    # Get the most recent draft
    latest = drafts[0]
    draft_id = latest.get("id")

    print(f"Publishing draft ID: {draft_id}")

    publish_draft(draft_id)

    print("Draft published successfully.")

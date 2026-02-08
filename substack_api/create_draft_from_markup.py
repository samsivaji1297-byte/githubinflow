# substack_api/create_draft_from_markup.py

import sys
import os
import json
from dotenv import load_dotenv
from draft_create import create_markup_draft

load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python create_draft_from_markup.py <markup_file>")
        sys.exit(1)

    markup_file = sys.argv[1]

    with open(markup_file, "r", encoding="utf-8") as f:
        markup_content = f.read().strip()

    # Create draft via existing helper
    draft = create_markup_draft(
        title=None,          # title is inside markup
        markup_content=markup_content,
        subtitle=None
    )

    # Log + persist ID
    draft_id = draft.get("id")
    print(f"Draft created with ID: {draft_id}")

    with open("draft_id.txt", "w", encoding="utf-8") as f:
        f.write(str(draft_id))

if __name__ == "__main__":
    main()

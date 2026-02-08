# substack_api/create_draft_from_markup.py

import sys
from draft_create import create_markup_draft

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_draft_from_markup.py <markup_file>")
        sys.exit(1)

    markup_file = sys.argv[1]

    with open(markup_file, "r", encoding="utf-8") as f:
        markup_content = f.read().strip()

    draft = create_markup_draft(
        title=None,  # title is included inside markup
        markup_content=markup_content,
        subtitle=None
    )

    print(f"Draft created: {draft}")

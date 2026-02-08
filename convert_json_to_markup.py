import json
import sys

def convert(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    # Build Substack markup
    parts = []

    if title:
        parts.append(f"Title:: {title}")

    if content:
        parts.append(f"Text:: {content}")

    # Join with Substack's pipe separator
    markup = " | ".join(parts)
    return markup


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_json_to_markup.py <path_to_json>")
        sys.exit(1)

    json_path = sys.argv[1]
    markup = convert(json_path)
    print(markup)

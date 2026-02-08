import json
import sys

def convert(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    # Build ProseMirror JSON structure
    doc = {
        "type": "doc",
        "content": []
    }

    # Title as H1
    if title:
        doc["content"].append({
            "type": "heading",
            "attrs": {"level": 1},
            "content": [{"type": "text", "text": title}]
        })

    # Body text as paragraph
    if content:
        doc["content"].append({
            "type": "paragraph",
            "content": [{"type": "text", "text": content}]
        })

    return doc


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_json_to_markup.py <path_to_json>")
        sys.exit(1)

    json_path = sys.argv[1]
    markup_json = convert(json_path)

    # Output ONLY valid JSON to stdout
    print(json.dumps(markup_json, ensure_ascii=False))

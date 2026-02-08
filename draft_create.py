# draft_create.py - Create Substack drafts
import os
import json
import requests
import re
from dotenv import load_dotenv

load_dotenv()

# Setup session
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": os.getenv("PUBLICATION_URL"),
    "Content-Type": "application/json"
})

# Set cookies
cookie_map = {
    "sid": os.getenv("SID"),
    "substack.lli": os.getenv("SUBSTACK_LLI"),
    "substack.sid": os.getenv("SUBSTACK_SID")
}
for k, v in cookie_map.items():
    if v:
        session.cookies.set(k, v, domain=".substack.com")

pub_url = os.getenv("PUBLICATION_URL")

def parse_markup_to_json(markup_text):
    """
    Parse user-friendly markup into Substack JSON content structure
    
    Markup Syntax:
    Title:: Main heading | Subtitle:: Optional subtitle | H1:: Heading 1 | H2:: Heading 2 |
    Text:: Regular text with **bold**, *italic*, ~~strikethrough~~, `code`, [link](url) |
    Quote:: Blockquote text | PullQuote:: Emphasized quote |
    List:: • Item 1 • Item 2 • Item 3 | NumberList:: 1. Item 1 1. Item 2 |
    Code:: python | print("hello") | Rule:: | Button:: Text -> url |
    Subscribe:: Button text | Share:: Button text | Comment:: Button text |
    SubscribeWidget:: Button >> Description | LaTeX:: E = mc^2 | Footnote:: [1] text
    """
    
    # Replace semicolons in content with commas to avoid conflicts
    markup_text = markup_text.replace(';', ',')
    
    # Split by main separator |
    blocks = [block.strip() for block in markup_text.split('|') if block.strip()]
    
    content = []
    footnote_counter = 1
    
    for block in blocks:
        if '::' not in block:
            # Treat as regular text if no type specified
            content.append({
                "type": "paragraph",
                "content": parse_inline_formatting(block)
            })
            continue
            
        block_type, block_content = block.split('::', 1)
        block_type = block_type.strip().lower()
        block_content = block_content.strip()
        
        if not block_content:
            continue
            
        if block_type == 'title':
            content.append({
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": block_content}]
            })
            
        elif block_type == 'subtitle':
            content.append({
                "type": "heading", 
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": block_content}]
            })
            
        elif block_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(block_type[1])
            content.append({
                "type": "heading",
                "attrs": {"level": level},
                "content": [{"type": "text", "text": block_content}]
            })
            
        elif block_type == 'text':
            content.append({
                "type": "paragraph",
                "content": parse_inline_formatting(block_content)
            })
            
        elif block_type == 'quote':
            content.append({
                "type": "blockquote",
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": block_content}]
                }]
            })
            
        elif block_type == 'pullquote':
            content.append({
                "type": "pullquote",
                "attrs": {"align": None, "color": None},
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": block_content}]
                }]
            })
            
        elif block_type == 'list':
            items = [item.strip() for item in block_content.split('•') if item.strip()]
            list_items = []
            for item in items:
                list_items.append({
                    "type": "list_item",
                    "content": [{
                        "type": "paragraph",
                        "content": parse_inline_formatting(item)
                    }]
                })
            content.append({
                "type": "bullet_list",
                "content": list_items
            })
            
        elif block_type == 'numberlist':
            # Split by numbers (1. 2. 3. etc.)
            items = re.split(r'\d+\.', block_content)[1:]  # Skip first empty element
            items = [item.strip() for item in items if item.strip()]
            list_items = []
            for item in items:
                list_items.append({
                    "type": "list_item",
                    "content": [{
                        "type": "paragraph",
                        "content": parse_inline_formatting(item)
                    }]
                })
            content.append({
                "type": "ordered_list",
                "attrs": {"start": 1, "order": 1},
                "content": list_items
            })
            
        elif block_type == 'code':
            # Format: language | code content
            parts = block_content.split('|', 1)
            if len(parts) == 2:
                language = parts[0].strip() or None
                code = parts[1].strip()
            else:
                language = None
                code = block_content
            
            content.append({
                "type": "code_block",
                "attrs": {"language": language},
                "content": [{"type": "text", "text": code}]
            })
            
        elif block_type == 'rule':
            content.append({"type": "horizontal_rule"})
            
        elif block_type == 'button':
            # Format: Button Text -> url
            if '->' in block_content:
                text, url = block_content.split('->', 1)
                text = text.strip()
                url = url.strip()
            else:
                text = block_content
                url = "#"
            
            content.append({
                "type": "button",
                "attrs": {
                    "url": url,
                    "text": text,
                    "action": None,
                    "class": None
                }
            })
            
        elif block_type == 'subscribe':
            content.append({
                "type": "button",
                "attrs": {
                    "url": "%%checkout_url%%",
                    "text": block_content,
                    "action": None,
                    "class": None
                }
            })
            
        elif block_type == 'share':
            content.append({
                "type": "button", 
                "attrs": {
                    "url": "%%share_url%%",
                    "text": block_content,
                    "action": None,
                    "class": None
                }
            })
            
        elif block_type == 'comment':
            content.append({
                "type": "button",
                "attrs": {
                    "url": "%%half_magic_comments_url%%",
                    "text": block_content,
                    "action": None,
                    "class": None
                }
            })
            
        elif block_type == 'subscribewidget':
            # Format: Button >> Description
            if '>>' in block_content:
                button_text, description = block_content.split('>>', 1)
                button_text = button_text.strip()
                description = description.strip()
            else:
                button_text = block_content
                description = "Subscribe for more content!"
                
            content.append({
                "type": "subscribeWidget",
                "attrs": {
                    "url": "%%checkout_url%%",
                    "text": button_text,
                    "language": "en"
                },
                "content": [{
                    "type": "ctaCaption",
                    "content": [{"type": "text", "text": description}]
                }]
            })
            
        elif block_type == 'sharewidget':
            # Format: Button >> Description
            if '>>' in block_content:
                button_text, description = block_content.split('>>', 1)
                button_text = button_text.strip()
                description = description.strip()
            else:
                button_text = block_content
                description = "Share this post!"
                
            content.append({
                "type": "captionedShareButton",
                "attrs": {
                    "url": "%%share_url%%",
                    "text": button_text
                },
                "content": [{
                    "type": "ctaCaption",
                    "content": [{"type": "text", "text": description}]
                }]
            })
            
        elif block_type == 'latex':
            content.append({
                "type": "latex_block",
                "attrs": {
                    "persistentExpression": block_content,
                    "id": f"EQUATION_{footnote_counter}"
                }
            })
            footnote_counter += 1
            
        elif block_type == 'footnote':
            # Format: [1] footnote text
            match = re.match(r'\[(\d+)\]\s*(.*)', block_content)
            if match:
                num = int(match.group(1))
                text = match.group(2)
                
                # Add footnote anchor in text (this should be done manually by user in Text:: blocks)
                # Add footnote definition at end
                content.append({
                    "type": "footnote",
                    "attrs": {"number": num},
                    "content": [{
                        "type": "paragraph", 
                        "content": [{"type": "text", "text": text}]
                    }]
                })
                
        elif block_type == 'break':
            content.append({"type": "paragraph"})
    
    return {"type": "doc", "content": content}


def parse_inline_formatting(text):
    """Parse inline formatting like **bold**, *italic*, [links](url), etc."""
    elements = []
    current_pos = 0
    
    # Patterns for different formatting
    patterns = [
        (r'\*\*(.*?)\*\*', 'strong'),      # **bold**
        (r'\*(.*?)\*', 'em'),              # *italic*  
        (r'~~(.*?)~~', 'strikethrough'),   # ~~strikethrough~~
        (r'`(.*?)`', 'code'),              # `code`
        (r'\[([^\]]+)\]\(([^)]+)\)', 'link')  # [text](url)
    ]
    
    # Find all formatting matches
    matches = []
    for pattern, format_type in patterns:
        for match in re.finditer(pattern, text):
            matches.append((match.start(), match.end(), format_type, match))
    
    # Sort by position
    matches.sort(key=lambda x: x[0])
    
    for start, end, format_type, match in matches:
        # Add text before this match
        if start > current_pos:
            plain_text = text[current_pos:start]
            if plain_text:
                elements.append({"type": "text", "text": plain_text})
        
        # Add formatted text
        if format_type == 'link':
            link_text = match.group(1)
            link_url = match.group(2)
            elements.append({
                "type": "text",
                "text": link_text,
                "marks": [{
                    "type": "link",
                    "attrs": {
                        "href": link_url,
                        "target": "_blank",
                        "rel": "noopener noreferrer nofollow",
                        "class": None
                    }
                }]
            })
        else:
            formatted_text = match.group(1)
            elements.append({
                "type": "text", 
                "text": formatted_text,
                "marks": [{"type": format_type}]
            })
        
        current_pos = end
    
    # Add remaining text
    if current_pos < len(text):
        remaining_text = text[current_pos:]
        if remaining_text:
            elements.append({"type": "text", "text": remaining_text})
    
    # If no formatting found, return simple text
    if not elements:
        elements = [{"type": "text", "text": text}]
    
    # CRITICAL FIX: Remove empty text elements that break Substack
    elements = [elem for elem in elements if elem.get('text', '').strip() != '']
    
    # If all elements were empty, return simple text
    if not elements:
        elements = [{"type": "text", "text": text}]
    
    return elements


def create_markup_draft(title, markup_content, subtitle=""):
    """Create a draft from user-friendly markup"""
    content_json = parse_markup_to_json(markup_content)
    return create_draft(title, subtitle, content_json=content_json)


def create_draft(title, subtitle="", content_text="", content_json=None):
    """Create a draft using the working method"""
    
    print(f"Creating draft: '{title}'")
    if subtitle:
        print(f"With subtitle: '{subtitle}'")
    if content_json:
        print(f"With JSON content: {len(content_json.get('content', []))} blocks")
        print(f"Content preview: {str(content_json)[:200]}...")
    elif content_text:
        print(f"With text content: {len(content_text)} characters")
    
    # Get existing drafts for reference
    drafts_response = session.get(f"{pub_url}/api/v1/drafts")
    if drafts_response.status_code != 200:
        print("Error: Can't get drafts")
        return None
        
    drafts = drafts_response.json()
    if len(drafts) == 0:
        print("Error: No existing drafts found. Create one manually first.")
        return None
    
    # Get reference draft structure - use UNPUBLISHED draft
    reference_id = None
    for draft in drafts:
        if not draft.get('is_published', False):
            reference_id = draft["id"]
            break
    
    if not reference_id:
        print("Error: No unpublished draft found for reference")
        return None
    
    ref_response = session.get(f"{pub_url}/api/v1/drafts/{reference_id}")
    if ref_response.status_code != 200:
        print("Error: Can't get reference draft")
        return None
    
    reference_draft = ref_response.json()
    print(f"Using unpublished draft {reference_id} as reference")
    
    # Create new draft data
    draft_data = reference_draft.copy()
    
    # Remove fields that shouldn't be copied
    remove_fields = ['id', 'uuid', 'created_at', 'updated_at', 'slug', 'draft_created_at', 'draft_updated_at']
    for field in remove_fields:
        draft_data.pop(field, None)
    
    # Set our new values
    draft_data['draft_title'] = title
    draft_data['draft_subtitle'] = subtitle if subtitle else None
    
    # Handle content
    if content_json:
        # Use provided JSON structure
        content_str = json.dumps(content_json)
        print(f"Setting draft_body to JSON with {len(content_str)} characters")
        draft_data['draft_body'] = content_str
    elif content_text:
        # Create simple paragraph from text
        content_structure = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": content_text}]
                }
            ]
        }
        content_str = json.dumps(content_structure)
        print(f"Setting draft_body to text paragraph with {len(content_str)} characters")
        draft_data['draft_body'] = content_str
    else:
        # Empty content
        print("Setting draft_body to empty content")
        draft_data['draft_body'] = '{"type":"doc","content":[]}'
    
    # Fix required fields
    draft_data['should_send_email'] = True
    draft_data['section_chosen'] = False  
    draft_data['subscriber_set_id'] = 1
    
    # THE KEY FIX: Set byline id = user_id
    draft_bylines = []
    for byline in reference_draft.get('postBylines', []):
        fixed_byline = {
            'user_id': byline['user_id'],
            'is_draft': True,
            'is_guest': byline.get('is_guest', False),
            'id': byline['user_id']  # MAGIC FIX: id = user_id
        }
        draft_bylines.append(fixed_byline)
    
    draft_data['draft_bylines'] = draft_bylines
    
    # Create the draft
    print(f"Sending POST request to create draft...")
    print(f"Draft data keys: {list(draft_data.keys())}")
    
    response = session.post(f"{pub_url}/api/v1/drafts", json=draft_data)
    
    if response.status_code == 200:
        draft = response.json()
        print(f"SUCCESS! Draft created with ID: {draft['id']}")
        print(f"Title: {draft.get('draft_title')}")
        print(f"Subtitle: {draft.get('draft_subtitle')}")
        
        # Check if content was actually saved
        if 'draft_body' in draft:
            body_content = draft['draft_body']
            if isinstance(body_content, str):
                try:
                    parsed_body = json.loads(body_content)
                    content_blocks = parsed_body.get('content', [])
                    print(f"Draft body contains {len(content_blocks)} content blocks")
                    for i, block in enumerate(content_blocks):
                        print(f"  Block {i}: {block.get('type', 'unknown')}")
                except Exception as e:
                    print(f"Draft body is string with {len(body_content)} characters")
                    print(f"JSON parse error: {e}")
        
        return draft
    else:
        print(f"FAILED: Status {response.status_code}")
        print(f"Response: {response.text}")
        return None

def create_comprehensive_test_draft(title="Complete Content Test", subtitle="Testing all Substack content types"):
    """Create a comprehensive test draft with ALL discovered content types"""
    
    user_id = os.getenv("USER_ID", "your_user_id")  # Get from env
    
    comprehensive_content = {
        "type": "doc",
        "content": [
            # H1-H6 Headings
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "H1: Main Heading"}]
            },
            {
                "type": "heading", 
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "H2: Section Heading"}]
            },
            {
                "type": "heading",
                "attrs": {"level": 3}, 
                "content": [{"type": "text", "text": "H3: Subsection"}]
            },
            
            # Text formatting paragraph
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Text formatting examples: "},
                    {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": ", "},
                    {"type": "text", "text": "italic", "marks": [{"type": "em"}]},
                    {"type": "text", "text": ", "},
                    {"type": "text", "text": "strikethrough", "marks": [{"type": "strikethrough"}]},
                    {"type": "text", "text": ", "},
                    {"type": "text", "text": "inline code", "marks": [{"type": "code"}]},
                    {"type": "text", "text": ", and "},
                    {
                        "type": "text", 
                        "text": "a link",
                        "marks": [{
                            "type": "link",
                            "attrs": {
                                "href": "https://example.com",
                                "target": "_blank",
                                "rel": "noopener noreferrer nofollow",
                                "class": None
                            }
                        }]
                    },
                    {"type": "text", "text": "."}
                ]
            },
            
            # Empty paragraph (line break)
            {"type": "paragraph"},
            
            # Block Quote
            {
                "type": "blockquote",
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "This is a block quote example."}]
                }]
            },
            
            # Pull Quote (emphasized)
            {
                "type": "pullquote",
                "attrs": {"align": None, "color": None},
                "content": [{
                    "type": "paragraph", 
                    "content": [{"type": "text", "text": "This is an emphasized pull quote."}]
                }]
            },
            
            # Bullet List
            {
                "type": "bullet_list",
                "content": [
                    {
                        "type": "list_item",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "First bullet point"}]
                        }]
                    },
                    {
                        "type": "list_item", 
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Second bullet point"}]
                        }]
                    },
                    {
                        "type": "list_item",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Third bullet point"}]
                        }]
                    }
                ]
            },
            
            # Numbered List
            {
                "type": "ordered_list",
                "attrs": {"start": 1, "order": 1},
                "content": [
                    {
                        "type": "list_item",
                        "content": [{
                            "type": "paragraph", 
                            "content": [{"type": "text", "text": "First numbered item"}]
                        }]
                    },
                    {
                        "type": "list_item",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Second numbered item"}] 
                        }]
                    }
                ]
            },
            
            # Code Block
            {
                "type": "code_block",
                "attrs": {"language": "python"},
                "content": [{
                    "type": "text",
                    "text": 'print("Hello, Substack!")\nfor i in range(3):\n    print(f"Item {i}")'
                }]
            },
            
            # Horizontal Rule
            {"type": "horizontal_rule"},
            
            {"type": "paragraph", "content": [{"type": "text", "text": "Content above and below the horizontal rule."}]},
            
            {"type": "horizontal_rule"},
            
            # Subscribe Button
            {
                "type": "button",
                "attrs": {
                    "url": "%%checkout_url%%", 
                    "text": "Subscribe Now",
                    "action": None,
                    "class": None
                }
            },
            
            # Subscribe Widget with Caption
            {
                "type": "subscribeWidget",
                "attrs": {
                    "url": "%%checkout_url%%",
                    "text": "Subscribe",
                    "language": "en"
                },
                "content": [{
                    "type": "ctaCaption",
                    "content": [{
                        "type": "text",
                        "text": "Thanks for reading! Subscribe for more content like this."
                    }]
                }]
            },
            
            # Share Button  
            {
                "type": "button",
                "attrs": {
                    "url": "%%share_url%%",
                    "text": "Share this post",
                    "action": None,
                    "class": None
                }
            },
            
            # Share Button with Caption
            {
                "type": "captionedShareButton",
                "attrs": {
                    "url": "%%share_url%%",
                    "text": "Share"
                },
                "content": [{
                    "type": "ctaCaption", 
                    "content": [{
                        "type": "text",
                        "text": "If you found this helpful, please share it with others!"
                    }]
                }]
            },
            
            # Custom Button
            {
                "type": "button",
                "attrs": {
                    "url": "https://github.com",
                    "text": "Visit GitHub",
                    "action": None,
                    "class": None
                }
            },
            
            # Comment Button
            {
                "type": "button", 
                "attrs": {
                    "url": "%%half_magic_comments_url%%",
                    "text": "Leave a comment",
                    "action": None,
                    "class": None
                }
            },
            
            # Direct Message Button
            {
                "type": "directMessage",
                "attrs": {
                    "userId": 370411012,  # Replace with your user ID
                    "userName": user_id,
                    "canDm": None,
                    "dmUpgradeOptions": None,
                    "isEditorNode": True,
                    "isEditor": True
                }
            },
            
            # LaTeX Block  
            {
                "type": "latex_block",
                "attrs": {
                    "persistentExpression": "E = mc^2",
                    "id": "EINSTEIN_EQUATION"
                }
            },
            
            # Footnote example
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "This statement needs a footnote"},
                    {"type": "footnoteAnchor", "attrs": {"number": 1}},
                    {"type": "text", "text": " to support it."}
                ]
            },
            
            {"type": "paragraph"},
            {"type": "paragraph"},
            
            # Footnote definition
            {
                "type": "footnote",
                "attrs": {"number": 1},
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": "This is the footnote explaining the statement above."
                    }]
                }]
            }
        ]
    }
    
    return create_draft(title, subtitle, content_json=comprehensive_content)


def create_rich_draft(title, subtitle=""):
    """Create a draft with basic rich formatting examples"""
    
    # Example rich content structure
    rich_content = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Welcome to my post"}]
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "This is "},
                    {"type": "text", "text": "bold text", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": " and this is "},
                    {"type": "text", "text": "italic text", "marks": [{"type": "em"}]},
                    {"type": "text", "text": "."}
                ]
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Check out "},
                    {"type": "text", "text": "this link", "marks": [{"type": "link", "attrs": {"href": "https://substack.com"}}]},
                    {"type": "text", "text": "!"}
                ]
            }
        ]
    }
    
    return create_draft(title, subtitle, content_json=rich_content)

if __name__ == "__main__":
    print("=== SUBSTACK DRAFT CREATION ===")
    print("\nChoose draft type:")
    print("1. Simple text draft (interactive)")
    print("2. Markup-based draft (user-friendly formatting)")
    print("3. Comprehensive test draft (all content types)")
    print("4. Basic rich formatting example")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        # Simple text draft (original functionality)
        title = input("\nEnter draft title: ")
        content = input("Enter draft content: ")
        
        if not title.strip():
            print("Error: Title cannot be empty")
            exit(1)
        
        if not content.strip():
            print("Error: Content cannot be empty") 
            exit(1)
        
        print(f"\nCreating draft with title: '{title}'")
        print(f"Content preview: '{content[:50]}{'...' if len(content) > 50 else ''}'")
        
        draft = create_draft(
            title=title,
            subtitle="",
            content_text=content
        )
        
    elif choice == "2":
        # Markup-based draft from sampleinput/2.txt
        sample_file = "sampleinput/2.txt"
        
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                markup_content = f.read().strip()
            
            # Clean up line breaks and extra spaces
            markup_content = markup_content.replace('\n', ' ').replace('\r', '')
            markup_content = ' '.join(markup_content.split())  # Remove extra whitespace
            
            print(f"\nReading markup content from: {sample_file}")
            print(f"Content preview: {markup_content[:100]}{'...' if len(markup_content) > 100 else ''}")
            
            # Extract title from markup or use default
            if "Title::" in markup_content:
                # Find the title in the markup
                title_part = markup_content.split("|")[0]
                title = title_part.replace("Title::", "").strip()
                
                # Check if title contains subtitle (format: Main Title: Subtitle)
                if ":" in title and not title.startswith("http"):
                    main_title, subtitle_part = title.split(":", 1)
                    title = main_title.strip()
                    subtitle = subtitle_part.strip()
                    print(f"Extracted title: '{title}'")
                    print(f"Extracted subtitle: '{subtitle}'")
                    
                    # Also modify the markup to use proper structure
                    modified_markup = markup_content.replace(
                        f"Title:: {main_title.strip()}: {subtitle_part.strip()}", 
                        f"Title:: {main_title.strip()} | Subtitle:: {subtitle_part.strip()}"
                    )
                    markup_content = modified_markup
                else:
                    subtitle = ""
            else:
                title = "Sample Markup Draft"
                subtitle = ""
            
            print(f"\nCreating markup draft with title: '{title}'")
            if subtitle:
                print(f"Subtitle: '{subtitle}'")
            print("Parsing markup...")
            print(f"Final markup content: {markup_content}")
            
            # Parse and show structure before creating
            content_json = parse_markup_to_json(markup_content)
            print(f"Parsed {len(content_json['content'])} content blocks")
            
            draft = create_markup_draft(title, markup_content, subtitle)
            
        except FileNotFoundError:
            print(f"Error: {sample_file} not found")
            print("Please create the file with your markup content")
            exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            exit(1)
        
    elif choice == "3":
        # Comprehensive test draft
        print("\nCreating comprehensive test draft with all content types...")
        draft = create_comprehensive_test_draft()
        
    elif choice == "4":
        # Basic rich formatting
        title = input("\nEnter draft title (or press Enter for default): ").strip()
        if not title:
            title = "Rich Formatting Example"
        
        print(f"\nCreating rich draft with title: '{title}'")
        draft = create_rich_draft(title)
        
    else:
        print("Invalid choice. Exiting.")
        exit(1)
    
    # Show results
    if draft:
        print(f"\nSUCCESS: Draft created with ID: {draft['id']}")
        print(f"Title: {draft.get('draft_title')}")
        print(f"URL: {pub_url}/publish/post/{draft['id']}?back=%2Fpublish%2Fposts%2Fdrafts")
        
        if choice == "2":
            print("\nMarkup draft created successfully!")
            print("Your markup was parsed and converted to rich Substack content.")
        elif choice == "3":
            print("\nThis comprehensive test draft includes:")
            print("- All heading levels (H1-H6)")  
            print("- Text formatting (bold, italic, strikethrough, code, links)")
            print("- Block quotes and pull quotes")
            print("- Bullet and numbered lists") 
            print("- Code blocks with syntax highlighting")
            print("- Horizontal rules")
            print("- Subscribe/share/comment buttons")
            print("- Direct message widget")
            print("- LaTeX equations")
            print("- Footnotes")
            print("- All interactive Substack elements")
    else:
        print("\nFAILED: Could not create draft")
    
    print("\nDraft creation complete!")
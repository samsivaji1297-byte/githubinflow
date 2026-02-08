# draft_publish.py - Publish Substack drafts
import os
import json
import requests
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

def get_drafts():
    """Get all drafts"""
    response = session.get(f"{pub_url}/api/v1/drafts")
    if response.status_code == 200:
        drafts = response.json()
        print(f"Found {len(drafts)} drafts")
        return drafts
    else:
        print(f"Error getting drafts: {response.text}")
        return []

def get_unpublished_drafts():
    """Get only unpublished drafts for API"""
    response = session.get(f"{pub_url}/api/v1/drafts")
    if response.status_code == 200:
        drafts = response.json()
        # Filter only unpublished drafts
        unpublished = [draft for draft in drafts if not draft.get('is_published', False)]
        return unpublished
    else:
        return None

def publish_draft(draft_id, send_email=True, audience="everyone"):
    """Publish a draft immediately"""
    
    print(f"Publishing draft {draft_id}...")
    print(f"Send email: {send_email}")
    print(f"Audience: {audience}")
    
    # Publish the draft
    publish_data = {
        "should_send_email": send_email,
        "audience": audience  # "everyone" or "paid"
    }
    
    response = session.post(f"{pub_url}/api/v1/drafts/{draft_id}/publish", json=publish_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"SUCCESS! Draft {draft_id} published!")
        
        # Get the published post URL if available
        post_url = None
        if 'slug' in result:
            post_url = f"{pub_url}/p/{result['slug']}"
            print(f"Post URL: {post_url}")
        
        # Return API-compatible format
        return {
            "success": True,
            "post_id": result.get('id'),
            "post_url": post_url,
            "message": f"Draft {draft_id} published successfully",
            "raw_result": result
        }
    else:
        print(f"FAILED to publish: {response.text}")
        return {
            "success": False,
            "message": f"Failed to publish draft {draft_id}: {response.text}",
            "error_code": response.status_code
        }

def publish_draft_paid_only(draft_id, send_email=True):
    """Publish a draft for paid subscribers only"""
    return publish_draft(draft_id, send_email=send_email, audience="paid")

def get_published_posts():
    """Get published posts"""
    response = session.get(f"{pub_url}/api/v1/posts")
    if response.status_code == 200:
        posts = response.json()
        print(f"Found {len(posts)} published posts")
        return posts
    else:
        print(f"Error getting posts: {response.text}")
        return []

def list_drafts():
    """List all drafts with details"""
    drafts = get_drafts()
    
    print("\n=== AVAILABLE DRAFTS ===")
    if not drafts:
        print("No drafts found")
        return []
    
    for draft in drafts:
        print(f"Draft ID: {draft['id']}")
        print(f"Title: {draft.get('draft_title', 'Untitled')}")
        print(f"Subtitle: {draft.get('draft_subtitle', 'No subtitle')}")
        print(f"Created: {draft.get('draft_created_at', 'Unknown')}")
        print(f"Updated: {draft.get('draft_updated_at', 'Unknown')}")
        
        # Show if scheduled
        if draft.get('post_date'):
            print(f"Scheduled for: {draft['post_date']}")
        
        # Show content preview
        draft_body = draft.get('draft_body', '{}')
        try:
            content = json.loads(draft_body)
            if content.get('content') and len(content['content']) > 0:
                first_paragraph = content['content'][0]
                if first_paragraph.get('content') and len(first_paragraph['content']) > 0:
                    first_text = first_paragraph['content'][0]
                    if first_text.get('text'):
                        preview = first_text['text'][:100]
                        print(f"Preview: {preview}...")
        except:
            print("Preview: [Content not readable]")
        
        print("-" * 50)
    
    return drafts

def unpublish_post(post_id):
    """Unpublish a post (make it a draft again)"""
    
    print(f"Unpublishing post {post_id}...")
    
    response = session.post(f"{pub_url}/api/v1/posts/{post_id}/unpublish", json={})
    
    if response.status_code == 200:
        result = response.json()
        print(f"SUCCESS! Post {post_id} unpublished (now a draft)")
        return result
    else:
        print(f"FAILED to unpublish: {response.text}")
        return None

def list_published_posts():
    """List published posts"""
    posts = get_published_posts()
    
    print("\n=== PUBLISHED POSTS ===")
    if not posts:
        print("No published posts found")
        return []
    
    for post in posts[:10]:  # Show first 10
        print(f"Post ID: {post['id']}")
        print(f"Title: {post.get('title', 'Untitled')}")
        print(f"Slug: {post.get('slug', 'no-slug')}")
        print(f"Published: {post.get('post_date', 'Unknown')}")
        
        if post.get('slug'):
            post_url = f"{pub_url}/p/{post['slug']}"
            print(f"URL: {post_url}")
        
        print("-" * 40)
    
    return posts

if __name__ == "__main__":
    print("=== SUBSTACK DRAFT PUBLISHING ===")
    
    # Get all drafts
    drafts = get_drafts()
    
    if not drafts:
        print("\nNo drafts found!")
        
        create_new = input("Do you want to create a new draft? (y/n): ").lower().strip()
        if create_new == 'y':
            print("\nCalling draft_create.py...")
            import subprocess
            import sys
            
            # Call draft_create.py
            result = subprocess.run([sys.executable, 'draft_create.py'], 
                                  cwd=os.path.dirname(os.path.abspath(__file__)))
            
            if result.returncode == 0:
                print("\nDraft created! Please run this script again to publish it.")
            else:
                print("\nFailed to create draft.")
        
        exit()
    
    # Show available drafts
    print(f"\n=== AVAILABLE DRAFTS ({len(drafts)}) ===")
    unpublished_drafts = []
    
    for i, draft in enumerate(drafts):
        if not draft.get('is_published', False):
            unpublished_drafts.append(draft)
            print(f"{len(unpublished_drafts)}. ID: {draft['id']}")
            print(f"   Title: {draft.get('draft_title', 'Untitled')}")
            
            # Show content preview
            draft_body = draft.get('draft_body', '{}')
            try:
                content = json.loads(draft_body)
                if content.get('content') and len(content['content']) > 0:
                    first_paragraph = content['content'][0]
                    if first_paragraph.get('content') and len(first_paragraph['content']) > 0:
                        first_text = first_paragraph['content'][0]
                        if first_text.get('text'):
                            preview = first_text['text'][:80]
                            print(f"   Preview: {preview}...")
            except:
                print("   Preview: [Content not readable]")
            print()
    
    if not unpublished_drafts:
        print("No unpublished drafts found!")
        
        create_new = input("Do you want to create a new draft? (y/n): ").lower().strip()
        if create_new == 'y':
            print("\nCalling draft_create.py...")
            import subprocess
            import sys
            
            result = subprocess.run([sys.executable, 'draft_create.py'], 
                                  cwd=os.path.dirname(os.path.abspath(__file__)))
            
            if result.returncode == 0:
                print("\nDraft created! Please run this script again to publish it.")
        
        exit()
    
    # Ask user to select a draft
    while True:
        try:
            choice = input(f"Select draft to publish (1-{len(unpublished_drafts)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("Goodbye!")
                exit()
            
            choice_num = int(choice) - 1
            if 0 <= choice_num < len(unpublished_drafts):
                selected_draft = unpublished_drafts[choice_num]
                break
            else:
                print(f"Invalid choice. Please enter 1-{len(unpublished_drafts)} or 'q'")
        except ValueError:
            print("Invalid input. Please enter a number or 'q'")
    
    # Show selected draft details
    print(f"\n=== SELECTED DRAFT ===")
    print(f"ID: {selected_draft['id']}")
    print(f"Title: {selected_draft.get('draft_title', 'Untitled')}")
    
    # Ask for publishing options
    print(f"\n=== PUBLISHING OPTIONS ===")
    
    # Email option
    send_email = input("Send email to subscribers? (y/n, default: y): ").lower().strip()
    send_email = send_email != 'n'
    
    # Audience option
    audience_choice = input("Audience (1=everyone, 2=paid only, default: 1): ").strip()
    audience = "paid" if audience_choice == "2" else "everyone"
    
    # Confirm
    print(f"\n=== CONFIRM PUBLISHING ===")
    print(f"Draft: {selected_draft.get('draft_title', 'Untitled')}")
    print(f"Send email: {send_email}")
    print(f"Audience: {audience}")
    
    confirm = input("\nPublish now? (y/n): ").lower().strip()
    
    if confirm == 'y':
        result = publish_draft(selected_draft['id'], send_email=send_email, audience=audience)
        
        if result:
            print(f"\nSUCCESS! Draft published!")
            if 'slug' in result:
                print(f"Post URL: {pub_url}/p/{result['slug']}")
        else:
            print(f"\nFAILED to publish draft.")
    else:
        print("Publishing cancelled.")
    
    print("\nPublishing complete!")
#!/usr/bin/env python3
"""
FastAPI server to expose Substack functionality as HTTP API endpoints
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
from dotenv import load_dotenv

# Import our existing functions
from draft_create import create_markup_draft, create_comprehensive_test_draft, parse_markup_to_json
from draft_publish import get_unpublished_drafts, publish_draft
from change_env import load_env_values, save_env_values
from multi_account import load_account_env, save_account_env, set_active_account_env, list_all_accounts

load_dotenv()

app = FastAPI(
    title="Substack API Client",
    description="API for creating and publishing Substack drafts with rich formatting",
    version="1.0.0"
)

# Pydantic models for request/response
class MarkupDraftRequest(BaseModel):
    user_id: str
    title: str
    markup_content: str
    subtitle: Optional[str] = ""

class PublishRequest(BaseModel):
    user_id: str
    draft_id: int
    send_email: bool = True
    audience: str = "everyone"  # "everyone" or "paid"

class DraftResponse(BaseModel):
    success: bool
    draft_id: Optional[int] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    url: Optional[str] = None
    message: str

class PublishResponse(BaseModel):
    success: bool
    post_id: Optional[int] = None
    post_url: Optional[str] = None
    message: str

class DraftInfo(BaseModel):
    id: int
    title: str
    subtitle: Optional[str]
    content_preview: str
    updated_at: Optional[str]

class EnvironmentUpdate(BaseModel):
    publication_url: Optional[str] = None
    user_id: Optional[str] = None
    sid: Optional[str] = None
    substack_sid: Optional[str] = None
    substack_lli: Optional[str] = None

class CookieUpdate(BaseModel):
    user_id: str  # Required to identify which account to update
    publication_url: Optional[str] = None
    sid: Optional[str] = None
    substack_sid: Optional[str] = None
    substack_lli: Optional[str] = None

class AccountInfo(BaseModel):
    user_id: str
    publication_url: str
    env_file: str

@app.get("/")
async def root():
    """API root endpoint with basic info"""
    return {
        "message": "Substack API Client",
        "version": "1.0.0",
        "endpoints": {
            "GET /accounts": "List all available accounts",
            "POST /drafts/create-markup": "Create draft from markup syntax (requires user_id)",
            "POST /drafts/create-test": "Create comprehensive test draft (requires user_id)",
            "GET /drafts": "List unpublished drafts (requires user_id parameter)",
            "POST /drafts/{draft_id}/publish": "Publish a draft (requires user_id in body)",
            "PUT /environment": "Update environment credentials",
            "POST /webhook/update-environment": "Update any environment variables (requires user_id)",
            "GET /docs": "Interactive API documentation"
        }
    }

@app.get("/accounts", response_model=List[AccountInfo])
async def list_accounts_api():
    """List all available Substack accounts"""
    try:
        accounts = list_all_accounts()
        return [AccountInfo(**acc) for acc in accounts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list accounts: {str(e)}")

@app.post("/drafts/create-markup", response_model=DraftResponse)
async def create_markup_draft_api(request: MarkupDraftRequest):
    """Create a draft using markup syntax for specific account"""
    try:
        # Load account environment
        try:
            set_active_account_env(request.user_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        # Parse markup to validate it
        try:
            content_json = parse_markup_to_json(request.markup_content)
            print(f"Parsed {len(content_json['content'])} content blocks for user {request.user_id}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid markup syntax: {str(e)}")
        
        # Create draft
        draft = create_markup_draft(request.title, request.markup_content, request.subtitle)
        
        if draft:
            pub_url = os.getenv("PUBLICATION_URL")
            return DraftResponse(
                success=True,
                draft_id=draft['id'],
                title=draft.get('draft_title'),
                subtitle=draft.get('draft_subtitle'),
                url=f"{pub_url}/publish/post/{draft['id']}?back=%2Fpublish%2Fposts%2Fdrafts",
                message=f"Draft created successfully with {len(content_json['content'])} content blocks for user {request.user_id}"
            )
        else:
            raise HTTPException(status_code=500, detail="Draft creation failed")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/drafts/create-test", response_model=DraftResponse)
async def create_test_draft_api(user_id: str):
    """Create a comprehensive test draft with all content types for specific account"""
    try:
        # Load account environment
        try:
            set_active_account_env(user_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        draft = create_comprehensive_test_draft()
        
        if draft:
            pub_url = os.getenv("PUBLICATION_URL")
            return DraftResponse(
                success=True,
                draft_id=draft['id'],
                title=draft.get('draft_title'),
                subtitle=draft.get('draft_subtitle'),
                url=f"{pub_url}/publish/post/{draft['id']}?back=%2Fpublish%2Fposts%2Fdrafts",
                message=f"Comprehensive test draft created with all content types for user {user_id}"
            )
        else:
            raise HTTPException(status_code=500, detail="Test draft creation failed")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/drafts", response_model=List[DraftInfo])
async def list_drafts_api(user_id: str):
    """List all unpublished drafts for specific account"""
    try:
        # Load account environment
        try:
            set_active_account_env(user_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        drafts = get_unpublished_drafts()
        
        if drafts is None:
            raise HTTPException(status_code=500, detail="Failed to fetch drafts")
        
        draft_list = []
        for draft in drafts:
            # Get content preview
            content_preview = "No content"
            if 'draft_body' in draft and draft['draft_body']:
                try:
                    import json
                    body = json.loads(draft['draft_body'])
                    content_blocks = body.get('content', [])
                    if content_blocks:
                        first_text = ""
                        for block in content_blocks:
                            if block.get('type') == 'paragraph' and block.get('content'):
                                for item in block['content']:
                                    if item.get('type') == 'text' and item.get('text'):
                                        first_text = item['text'][:100]
                                        break
                                if first_text:
                                    break
                        content_preview = first_text or f"{len(content_blocks)} content blocks"
                except:
                    content_preview = "Content available"
            
            draft_list.append(DraftInfo(
                id=draft['id'],
                title=draft.get('draft_title', 'Untitled'),
                subtitle=draft.get('draft_subtitle'),
                content_preview=content_preview,
                updated_at=draft.get('draft_updated_at')
            ))
        
        return draft_list
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/drafts/{draft_id}/publish", response_model=PublishResponse)
async def publish_draft_api(draft_id: int, request: PublishRequest):
    """Publish a specific draft for specific account"""
    try:
        # Load account environment
        try:
            set_active_account_env(request.user_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        result = publish_draft(
            draft_id=draft_id,
            send_email=request.send_email,
            audience=request.audience
        )
        
        if result and result.get('success'):
            return PublishResponse(
                success=True,
                post_id=result.get('post_id'),
                post_url=result.get('post_url'),
                message=result.get('message', f'Draft published successfully for user {request.user_id}')
            )
        else:
            error_msg = result.get('message', 'Publishing failed') if result else 'Publishing failed'
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.put("/environment")
async def update_environment_api(request: EnvironmentUpdate):
    """Update environment credentials"""
    try:
        # Load current values
        current_values = load_env_values()
        
        # Update with provided values
        updated_values = current_values.copy()
        
        if request.publication_url is not None:
            updated_values['PUBLICATION_URL'] = request.publication_url
        if request.user_id is not None:
            updated_values['USER_ID'] = request.user_id
        if request.sid is not None:
            updated_values['SID'] = request.sid
        if request.substack_sid is not None:
            updated_values['SUBSTACK_SID'] = request.substack_sid
        if request.substack_lli is not None:
            updated_values['SUBSTACK_LLI'] = request.substack_lli
        
        # Save updated values
        save_env_values(updated_values)
        
        # Reload environment
        load_dotenv()
        
        return {
            "success": True,
            "message": "Environment updated successfully",
            "updated_fields": [k.lower() for k, v in request.dict().items() if v is not None]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update environment: {str(e)}")

@app.get("/markup-syntax")
async def get_markup_syntax():
    """Get markup syntax guide"""
    return {
        "basic_format": "Type:: Content | Type:: Content | Type:: Content",
        "content_types": {
            "Title::": "Main heading (H1)",
            "Subtitle::": "Secondary heading (H2)",
            "H1:: - H6::": "Custom heading levels",
            "Text::": "Paragraph with **bold**, *italic*, [links](url)",
            "Quote::": "Block quote",
            "PullQuote::": "Emphasized quote",
            "List::": "Bullet list (• separated)",
            "NumberList::": "Numbered list (1. 2. 3.)",
            "Code::": "Code block (language | code)",
            "Rule::": "Horizontal divider",
            "Button::": "Custom button (text -> url)",
            "Subscribe::": "Subscribe button",
            "Share::": "Share button",
            "Comment::": "Comment button",
            "SubscribeWidget::": "Subscribe with description (button >> description)",
            "LaTeX::": "Mathematical equations",
            "Break::": "Empty paragraph/line break"
        },
        "inline_formatting": {
            "**text**": "Bold text",
            "*text*": "Italic text",
            "~~text~~": "Strikethrough text",
            "`code`": "Inline code",
            "[text](url)": "Link"
        },
        "example": "Title:: My Post | Text:: Welcome with **bold** text and a [link](https://example.com) | Quote:: This is important | Subscribe:: Join Now"
    }

@app.post("/webhook/update-environment")
async def update_environment_webhook(request: CookieUpdate):
    """
    Webhook endpoint for updating any environment variables for specific account.
    Should be protected by Cloudflare Access rules to allow only authorized sources.
    All parameters are optional except user_id - only provided values will be updated.
    """
    try:
        # Load current account environment values
        try:
            current_values = load_account_env(request.user_id)
        except ValueError:
            # Account doesn't exist, create new one with provided values
            current_values = {'USER_ID': request.user_id}
        
        # Track what gets updated
        updated_fields = []
        
        # Update only provided values
        if request.publication_url is not None:
            current_values['PUBLICATION_URL'] = request.publication_url
            updated_fields.append("publication_url")
            
        if request.sid is not None:
            current_values['SID'] = request.sid
            updated_fields.append("sid")
            
        if request.substack_sid is not None:
            current_values['SUBSTACK_SID'] = request.substack_sid
            updated_fields.append("substack_sid")
            
        if request.substack_lli is not None:
            current_values['SUBSTACK_LLI'] = request.substack_lli
            updated_fields.append("substack_lli")
        
        # Check if anything was actually updated (besides user_id)
        if not updated_fields:
            return {
                "success": True,
                "message": f"No changes made for user {request.user_id} - no values provided",
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "user_id": request.user_id,
                "updated_fields": []
            }
        
        # Save updated values for this account
        env_file = save_account_env(request.user_id, current_values)
        
        return {
            "success": True,
            "message": f"Environment updated successfully for user {request.user_id} - {len(updated_fields)} field(s) changed",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "user_id": request.user_id,
            "env_file": env_file,
            "updated_fields": updated_fields
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update environment for user {request.user_id}: {str(e)}")

if __name__ == "__main__":
    print("Starting Substack API Server...")
    print("API documentation available at: http://localhost:8000/docs")
    print("API root: http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
#!/usr/bin/env python3
"""
Interactive script to update .env file with Substack authentication values.
Press Enter to keep existing values unchanged.
"""

import os
from pathlib import Path

def load_env_values():
    """Load current values from .env file"""
    env_path = Path('.env')
    env_values = {}
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_values[key] = value
    
    return env_values

def save_env_values(values):
    """Save values to .env file"""
    with open('.env', 'w') as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")

def get_user_input(prompt, current_value=None):
    """Get user input with current value as default"""
    if current_value:
        user_input = input(f"{prompt} (current: {current_value[:50]}{'...' if len(current_value) > 50 else ''}): ").strip()
        return user_input if user_input else current_value
    else:
        return input(f"{prompt}: ").strip()

def main():
    print("=== Substack Environment Configuration ===\n")
    
    # Load existing values
    current_values = load_env_values()
    
    # Collect new values
    env_values = {}
    
    print("Update your Substack authentication settings:")
    print("Press Enter to keep current values unchanged.\n")
    
    env_values['PUBLICATION_URL'] = get_user_input(
        "Publication URL (e.g., https://yourname.substack.com)", 
        current_values.get('PUBLICATION_URL')
    )
    
    env_values['USER_ID'] = get_user_input(
        "User ID (your Substack username)", 
        current_values.get('USER_ID')
    )
    
    env_values['SID'] = get_user_input(
        "SID cookie value", 
        current_values.get('SID')
    )
    
    env_values['SUBSTACK_SID'] = get_user_input(
        "SUBSTACK_SID cookie value", 
        current_values.get('SUBSTACK_SID')
    )
    
    env_values['SUBSTACK_LLI'] = get_user_input(
        "SUBSTACK_LLI cookie value", 
        current_values.get('SUBSTACK_LLI')
    )
    
    # Save to .env file
    save_env_values(env_values)
    
    print(f"\n✅ Environment configuration saved to .env")
    print(f"📝 Publication: {env_values['PUBLICATION_URL']}")
    print(f"👤 User: {env_values['USER_ID']}")
    
    print("\n=== How to get authentication values ===")
    print("1. Login to your Substack account in browser")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Application/Storage → Cookies → https://substack.com")
    print("4. Find cookies: 'sid', 'substack.sid', 'substack.lli'")
    print("5. Copy their values (right-click → copy)")
    print("6. Your USER_ID is your Substack username")
    print("7. PUBLICATION_URL is your publication's homepage URL")

if __name__ == "__main__":
    main()
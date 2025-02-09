import os
import json
import browser_cookie3
import jwt
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_google_cookies():
    """Extract Google cookies from Chrome browser."""
    try:
        logger.debug("Starting cookie extraction...")
        
        # Get cookies from Chrome
        cookies = browser_cookie3.chrome(domain_name='.google.com')
        
        cookie_dict = {}
        auth_tokens = {}
        
        for cookie in cookies:
            cookie_dict[cookie.name] = cookie.value
            # Look specifically for authentication related cookies
            if any(key in cookie.name.lower() for key in ['auth', 'sid', 'hsid', 'ssid', 'apisid']):
                auth_tokens[cookie.name] = cookie.value
                logger.debug(f"Found auth cookie: {cookie.name}")
        
        # Save all cookies
        with open('cookies.json', 'w') as f:
            json.dump(cookie_dict, f, indent=2)
        logger.info("✓ Saved cookies to cookies.json")
        
        # Save auth tokens to .env
        if auth_tokens:
            env_content = []
            # Read existing .env content
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    env_content = f.readlines()
            
            # Update or add GOOGLE_AUTH_TOKEN
            token_line = f"GOOGLE_AUTH_TOKEN={list(auth_tokens.values())[0]}\n"
            token_updated = False
            
            for i, line in enumerate(env_content):
                if line.startswith('GOOGLE_AUTH_TOKEN='):
                    env_content[i] = token_line
                    token_updated = True
                    break
            
            if not token_updated:
                env_content.append(token_line)
            
            with open('.env', 'w') as f:
                f.writelines(env_content)
            
            logger.info("✓ Updated .env with auth token")
            return cookie_dict
            
        else:
            logger.error("No authentication tokens found")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting cookies: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    print("Extracting Google authentication data...")
    extract_google_cookies()

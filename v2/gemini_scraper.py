import asyncio
import json
import logging
import os
import random
from datetime import datetime
from dotenv import load_dotenv
from fake_useragent import UserAgent
from pathlib import Path
from cryptography.fernet import Fernet
from playwright.async_api import async_playwright, Browser, Page
from typing import List, Dict, Optional
from aiolimiter import AsyncLimiter

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GeminiScraper:
    @classmethod
    async def create(cls):
        instance = cls()
        await instance.setup()
        return instance

    def __init__(self):
        self.cipher = Fernet(os.getenv('ENCRYPTION_KEY'))
        self.ua = UserAgent()
        self.proxy_pool = json.loads(os.getenv('PROXY_POOL', '[]'))
        self.current_proxy = None
        self.urls = [
            os.getenv('GEMINI_URL'),
            os.getenv('ACTIVITY_URL')
        ]
        self.browser = None
        self.context = None
        self.page = None
        self.sid_cookie = None
        self.limiter = AsyncLimiter(
            max_rate=int(os.getenv('RATE_LIMIT_REQUESTS', 30)),
            time_period=int(os.getenv('RATE_LIMIT_SECONDS', 60))
        )

    async def rotate_proxy(self):
        self.current_proxy = random.choice(self.proxy_pool) if self.proxy_pool else None
        logger.info(f'Rotated to proxy: {self.current_proxy}')

    async def setup(self) -> None:
        """Initialize Playwright browser"""
        try:
            logger.debug("Starting Playwright browser...")
            await self.rotate_proxy()
            playwright = await async_playwright().start()
            proxy = {
                'server': self.current_proxy,
                'username': os.getenv('PROXY_USER'),
                'password': os.getenv('PROXY_PASS')
            } if self.current_proxy else None

            self.browser = await playwright.chromium.launch(
                headless=True,  # Set to True for production
                proxy=proxy,
                args=[
                    f'--user-agent={self.ua.random}',
                    f'--window-size={random.randint(800,1920)},{random.randint(600,1080)}'
                ]
            )
            # Use existing browser context
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0 Safari/537.36"
            )
            self.page = await self.context.new_page()
            logger.info("Browser setup complete")

            # Intercept network responses
            async def handle_response(response):
                headers = response.headers
                set_cookie_header = headers.get('set-cookie')

                if set_cookie_header:
                    # Check if the Set-Cookie header contains the SID cookie
                    if isinstance(set_cookie_header, list):
                        sid_cookie = next((cookie for cookie in set_cookie_header if cookie.startswith('SID=')), None)
                    else:
                        sid_cookie = set_cookie_header if set_cookie_header.startswith('SID=') else None
                    if sid_cookie:
                        # Extract the SID value
                        sid_value = sid_cookie.split(';')[0].split('=')[1]
                        logger.info('Extracted SID: %s', sid_value)
                        self.sid_cookie = sid_value
                        # You can now store this value and use it later
                        await self.store_cookie(sid_value)

            self.page.on('response', handle_response)

        except Exception as e:
            logger.error(f"Failed to setup browser: {str(e)}", exc_info=True)
            raise

    async def store_cookie(self, sid):
        encrypted = self.cipher.encrypt(sid.encode())
        with open('.session', 'wb') as f:
            f.write(encrypted)

    async def load_cookie(self):
        try:
            with open('.session', 'rb') as f:
                return self.cipher.decrypt(f.read()).decode()
        except FileNotFoundError:
            return None

    async def inject_cookies(self, cookies_file: str) -> None:
        """Load and inject cookies from file"""
        try:
            logger.debug(f"Loading cookies from {cookies_file}")
            cookies_path = Path(cookies_file)
            if not cookies_path.exists():
                raise FileNotFoundError(f"Cookies file not found: {cookies_file}")

            with open(cookies_path, 'r') as f:
                cookies = json.load(f)
                
            # Convert cookies to Playwright format
            playwright_cookies = []
            for name, value in cookies.items():
                playwright_cookies.append({
                    'name': name,
                    'value': value,
                    'domain': '.google.com',
                    'path': '/'
                })
                
            await self.context.add_cookies(playwright_cookies)
            logger.info("Cookies injected successfully")
        except Exception as e:
            logger.error(f"Failed to inject cookies: {str(e)}", exc_info=True)
            raise

    async def wait_for_conversations(self) -> None:
        """Wait for conversation elements to load"""
        selectors = [
            # Main containers
            ".conversation-items-container",
            ".conversations-container",
            ".chat-container",
            
            # Individual items
            ".mat-mdc-tooltip-trigger.conversation",
            ".conversation-actions-container",
            
            # Chat content
            "chat-window-content",
            "input-container",
            
            # Fallback selectors
            "[data-test-id]",
            "[jslog]"
        ]
        
        for selector in selectors:
            try:
                logger.debug(f"Trying selector: {selector}")
                await self.page.wait_for_selector(selector, timeout=5000)
                logger.info(f"Found conversations using selector: {selector}")
                return selector
            except Exception:
                continue
                
        raise TimeoutError("Could not find conversation elements")

    async def extract_conversations(self) -> List[Dict[str, str]]:
        """Extract conversations from the page"""
        try:
            logger.debug("Starting conversation extraction")
            selector = await self.wait_for_conversations()
            
            conversations = []
            
            # Try to find conversation list items
            elements = await self.page.query_selector_all(".mat-mdc-tooltip-trigger.conversation")
            
            if not elements:
                logger.warning(f"No elements found with selector: {selector}")
                return []
                
            logger.info(f"Found {len(elements)} potential conversation elements")
            
            for element in elements:
                try:
                    # Get conversation title from label span
                    title = ""
                    title_element = await element.query_selector(".mdc-button__label")
                    if title_element:
                        title = await title_element.text_content()
                    
                    # Get conversation content
                    content = await element.text_content()
                    
                    # Try to find timestamp from jslog attribute
                    timestamp = None
                    jslog = await element.get_attribute("jslog")
                    if jslog and "timestamp" in jslog:
                        timestamp = jslog.split("timestamp=")[1].split(";")[0]
                    else:
                        timestamp = datetime.now().isoformat()
                    
                    # Skip empty or very short content
                    if len(content.strip()) > 10:  # Minimum content length
                        conversation = {
                            'timestamp': timestamp,
                            'content': content.strip()
                        }
                        if title:
                            conversation['title'] = title.strip()
                        conversations.append(conversation)
                        logger.debug(f"Extracted conversation: {title or 'Untitled'}")
                except Exception as e:
                    logger.warning(f"Failed to extract conversation: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(conversations)} conversations")
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to extract conversations: {str(e)}", exc_info=True)
            return []

    async def safe_request(self, url):
        async with self.limiter:
            logger.info('Making request to %s', url)
            response = await self.page.goto(url)
            await self.page.wait_for_timeout(1000)  # Default delay
            return response

    async def scrape(self, cookies_file: Optional[str] = None) -> List[Dict[str, str]]:
        """Main scraping method"""
        try:
            sid_cookie = await self.load_cookie()
            if sid_cookie:
                self.sid_cookie = sid_cookie
                logger.info("Loaded SID cookie from storage")
            
            if not self.sid_cookie:
                await self.setup()
            
            if cookies_file:
                await self.inject_cookies(cookies_file)
            
            all_conversations = []
            
            # Try each URL
            for url in self.urls:
                try:
                    logger.debug(f"Trying URL: {url}")
                    await self.safe_request(url)
                    
                    # Wait for authentication and content to load
                    await self.page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)  # Give dynamic content time to load
                    
                    # For PWA, try to expand the conversation list
                    if "gemini.google.com" in url:
                        try:
                            # Click show more button while it exists
                            show_more_selector = "[data-test-id='show-more-button']"
                            while True:
                                try:
                                    show_more = await self.page.wait_for_selector(show_more_selector, timeout=2000)
                                    if show_more:
                                        await show_more.click()
                                        await asyncio.sleep(1)  # Wait for new items to load
                                except:
                                    break
                                    
                        except Exception as e:
                            logger.debug(f"No more items to load: {str(e)}")
                    
                    conversations = await self.extract_conversations()
                    if conversations:
                        all_conversations.extend(conversations)
                        logger.info(f"Found {len(conversations)} conversations at {url}")
                    else:
                        logger.warning(f"No conversations found at {url}")
                        
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {str(e)}")
                    continue
            
            if all_conversations:
                # Remove duplicates based on content
                seen = set()
                unique_conversations = []
                for conv in all_conversations:
                    content = conv['content']
                    if content not in seen:
                        seen.add(content)
                        unique_conversations.append(conv)
                
                # Save to file
                output_file = 'gemini_conversations.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(unique_conversations, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved {len(unique_conversations)} unique conversations to {output_file}")
                
                return unique_conversations
            else:
                logger.warning("No conversations found at any URL")
                return []
            
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}", exc_info=True)
            return []
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    scraper = await GeminiScraper.create()
    await scraper.scrape(cookies_file="cookies.json")

if __name__ == "__main__":
    asyncio.run(main())

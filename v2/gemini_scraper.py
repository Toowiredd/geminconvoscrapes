import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page
from typing import List, Dict, Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GeminiScraper:
    def __init__(self):
        self.url = "https://myactivity.google.com/product/gemini"
        self.browser = None
        self.context = None
        self.page = None

    async def setup(self) -> None:
        """Initialize Playwright browser"""
        try:
            logger.debug("Starting Playwright browser...")
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=False,  # Set to True for production
            )
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            logger.info("Browser setup complete")
        except Exception as e:
            logger.error(f"Failed to setup browser: {str(e)}", exc_info=True)
            raise

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
            "article",  # Most likely container for conversation items
            "[role='article']",
            ".activity-item",
            ".conversation-item",
            "[data-conversation]"
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
            
            # Get all conversation elements
            conversations = []
            elements = await self.page.query_selector_all(selector)
            
            for element in elements:
                try:
                    # Extract timestamp and content
                    timestamp = await element.query_selector("time")
                    content = await element.text_content()
                    
                    if timestamp:
                        timestamp_text = await timestamp.text_content()
                    else:
                        timestamp_text = datetime.now().isoformat()
                    
                    conversations.append({
                        'timestamp': timestamp_text,
                        'content': content.strip()
                    })
                    logger.debug(f"Extracted conversation with timestamp: {timestamp_text}")
                except Exception as e:
                    logger.warning(f"Failed to extract conversation: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(conversations)} conversations")
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to extract conversations: {str(e)}", exc_info=True)
            return []

    async def scrape(self, cookies_file: Optional[str] = None) -> List[Dict[str, str]]:
        """Main scraping method"""
        try:
            await self.setup()
            
            if cookies_file:
                await self.inject_cookies(cookies_file)
            
            logger.debug(f"Navigating to {self.url}")
            await self.page.goto(self.url)
            
            # Wait for authentication
            await self.page.wait_for_load_state('networkidle')
            
            conversations = await self.extract_conversations()
            
            if conversations:
                # Save to file
                output_file = 'gemini_conversations.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(conversations, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved {len(conversations)} conversations to {output_file}")
            
            return conversations
            
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}", exc_info=True)
            return []
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    scraper = GeminiScraper()
    await scraper.scrape(cookies_file="cookies.json")

if __name__ == "__main__":
    asyncio.run(main())

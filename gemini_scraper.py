import os
import json
import time
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GeminiScraper:
    def __init__(self, cookies_file=None):
        self.url = "https://myactivity.google.com/product/gemini"
        self.driver = None
        self.cookies_file = cookies_file
        load_dotenv()
        
    def setup_driver(self):
        """Initialize the Chrome WebDriver with appropriate options"""
        logger.debug("Setting up Chrome WebDriver...")
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment for headless mode
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome WebDriver setup successful")
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {str(e)}", exc_info=True)
            raise
        
    def load_cookies(self):
        """Load cookies from file if provided"""
        if not self.cookies_file or not os.path.exists(self.cookies_file):
            logger.warning("No cookies file found")
            return False
            
        try:
            logger.debug("Loading cookies from file...")
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            logger.info("Cookies loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load cookies: {str(e)}", exc_info=True)
            return False

    def login(self):
        """Handle login process"""
        logger.debug("Starting login process...")
        auth_token = os.getenv("GOOGLE_AUTH_TOKEN")
        if not auth_token:
            logger.error("No authentication token found in .env file")
            raise ValueError("Authentication token not found")
        
        try:
            # Add authentication token to browser
            self.driver.add_cookie({
                'name': 'AUTH_TOKEN',
                'value': auth_token,
                'domain': '.google.com'
            })
            logger.info("Authentication token added successfully")
        except Exception as e:
            logger.error(f"Failed to add authentication token: {str(e)}", exc_info=True)
            raise

    def scrape_conversations(self):
        """Scrape Gemini conversation history"""
        logger.debug("Starting conversation scraping...")
        try:
            self.driver.get(self.url)
            logger.debug(f"Navigated to {self.url}")
            
            # Wait for the activity feed to load
            wait = WebDriverWait(self.driver, 20)
            logger.debug("Waiting for activity items to load...")
            
            try:
                activity_items = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".activity-item"))
                )
                logger.info(f"Found {len(activity_items)} activity items")
            except TimeoutException:
                logger.warning("No activity items found, trying alternative selectors...")
                # Try alternative selectors
                selectors = [
                    ".conversation-item",
                    "[data-conversation]",
                    ".chat-message"
                ]
                for selector in selectors:
                    try:
                        activity_items = wait.until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                        )
                        if activity_items:
                            logger.info(f"Found {len(activity_items)} items using selector: {selector}")
                            break
                    except TimeoutException:
                        continue
            
            conversations = []
            for item in activity_items:
                try:
                    timestamp = item.find_element(By.CSS_SELECTOR, ".timestamp").text
                    content = item.find_element(By.CSS_SELECTOR, ".content").text
                    conversations.append({
                        'timestamp': timestamp,
                        'content': content
                    })
                    logger.debug(f"Extracted conversation with timestamp: {timestamp}")
                except NoSuchElementException as e:
                    logger.warning(f"Failed to extract conversation item: {str(e)}")
                    
            logger.info(f"Successfully scraped {len(conversations)} conversations")
            return conversations
                    
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}", exc_info=True)
            return []

    def save_conversations(self, conversations, output_file='gemini_conversations.json'):
        """Save scraped conversations to a JSON file"""
        try:
            logger.debug(f"Saving conversations to {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(conversations, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully saved {len(conversations)} conversations to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save conversations: {str(e)}", exc_info=True)
            raise

    def run(self, output_file='gemini_conversations.json'):
        """Main execution method"""
        try:
            logger.info("Starting Gemini scraping process")
            self.setup_driver()
            
            if self.cookies_file:
                self.load_cookies()
            else:
                self.login()
                
            conversations = self.scrape_conversations()
            if conversations:
                self.save_conversations(conversations, output_file)
                return conversations
            else:
                logger.warning("No conversations were scraped")
                return []
            
        except Exception as e:
            logger.error(f"Scraping process failed: {str(e)}", exc_info=True)
            raise
        finally:
            if self.driver:
                logger.debug("Closing Chrome WebDriver")
                self.driver.quit()

if __name__ == "__main__":
    scraper = GeminiScraper(cookies_file="cookies.json")
    scraper.run()

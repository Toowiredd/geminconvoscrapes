from abc import ABC, abstractmethod
from typing import Dict, Any
import json
from stealth import Stealth

class BaseScraper(ABC):
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = json.load(f)
        
    @abstractmethod
    async def authenticate(self):
        pass

    @abstractmethod
    async def extract_data(self):
        pass

    async def stealth_setup(self):
        stealth = Stealth(self.page)
        stealth.randomize_user_agent()
        stealth.disable_webdriver()
        await stealth.apply()

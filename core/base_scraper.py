from abc import ABC, abstractmethod
from typing import Dict, Any
import json
import os
import sys
import subprocess
from stealth import Stealth
import psutil

from core.exceptions import ScraperConfigurationError, ResourceThresholdExceededError

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

    def pre_scrape_check(self):
        # Existing checks
        if not self.docker_host_available():  # New check
            raise ScraperConfigurationError("Docker host unavailable")
        # Original resource checks
        if psutil.virtual_memory().percent > 90:
            raise ResourceThresholdExceededError

    def docker_host_available(self):
        try:
            subprocess.run(['docker', 'info'], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

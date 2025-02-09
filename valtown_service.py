import aiohttp
import asyncio
import json
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class ValTownService:
    def __init__(self):
        self.api_key = os.getenv("VALTOWN_API_KEY")
        self.base_url = "https://api.val.town/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def create_val(self, name: str, code: str) -> Dict:
        """Create a new Val function"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/vals"
            payload = {
                "name": name,
                "code": code,
                "public": True
            }
            async with session.post(url, headers=self.headers, json=payload) as response:
                return await response.json()

    async def run_val(self, username: str, val_name: str, args: Optional[List] = None) -> Dict:
        """Run a Val function"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/eval/@{username}/{val_name}"
            payload = {"args": args or []}
            async with session.post(url, headers=self.headers, json=payload) as response:
                return await response.json()

    async def store_conversations(self, conversations: List[Dict]) -> str:
        """Store conversations in Val.Town and return the URL"""
        # Create a Val function to store and serve the conversations
        store_code = f"""
        export const conversations = {json.dumps(conversations)};
        export async function getConversations() {{
            return conversations;
        }}
        """
        
        val_name = "gemini_conversations"
        result = await self.create_val(val_name, store_code)
        return f"https://val.town/v/{result['author']}/{val_name}"

    async def get_conversations(self, username: str) -> List[Dict]:
        """Retrieve conversations from Val.Town"""
        result = await self.run_val(username, "gemini_conversations")
        return result.get("data", [])

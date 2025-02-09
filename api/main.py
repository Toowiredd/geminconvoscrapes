from fastapi import FastAPI, Security, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import asyncio
from typing import List
from importlib import import_module
import uuid

app = FastAPI(title="Scraper API")
security = HTTPBearer()

class ScrapeRequest(BaseModel):
    urls: List[str]
    proxy_group: str = 'default'

@app.post('/scrape/{site}')
async def scrape_site(site: str, request: ScrapeRequest, token: str = Security(security)):
    """Initiate new scraping job with proxy rotation"""
    try:
        module = import_module(f'sites.{site}.scraper')
        scraper = module.Scraper()
        job_id = str(uuid.uuid4())
        asyncio.create_task(scraper.scrape(request.urls))
        return {'job_id': job_id}
    except ModuleNotFoundError:
        raise HTTPException(status_code=404, detail=f"Site '{site}' not found")

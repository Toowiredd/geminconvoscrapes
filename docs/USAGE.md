# Gemini Scraper Documentation

## Rate Limiting Configuration

```bash
# Environment Variables
RATE_LIMIT_REQUESTS=30  # Max requests per minute
RATE_LIMIT_SECONDS=60    # Time window in seconds
RETRY_ATTEMPTS=3         # Max retries on rate limit errors
```

## Basic Usage

```python
from gemini_scraper import GeminiScraper
import asyncio

async def main():
    scraper = await GeminiScraper.create()
    
    # Scrape with default rate limits
    await scraper.scrape()

    # Scrape specific conversation with custom limits
    await scraper.scrape_conversation("abc123", 
        rate_limit=10,  # requests
        period=30       # seconds
    )

asyncio.run(main())
```

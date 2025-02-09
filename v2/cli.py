import typer
import asyncio
import logging
from gemini_scraper import GeminiScraper
from gemini_tui import GeminiTUI

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def scrape(cookies_file: str = "cookies.json"):
    """Scrape Gemini conversations using Playwright"""
    try:
        scraper = GeminiScraper()
        asyncio.run(scraper.scrape(cookies_file=cookies_file))
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}", exc_info=True)
        raise typer.Exit(1)

@app.command()
def interactive():
    """Launch interactive TUI"""
    try:
        app = GeminiTUI()
        app.run()
    except Exception as e:
        logger.error(f"TUI failed to start: {str(e)}", exc_info=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()

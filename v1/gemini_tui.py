from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Button, Static, DataTable, Label, LoadingIndicator, Log
from textual.binding import Binding
from textual.reactive import reactive
from textual import work
from rich.console import Console
from datetime import datetime
import json
import asyncio
import logging
from pathlib import Path
from extract_token import extract_google_cookies
from gemini_scraper import GeminiScraper
from valtown_service import ValTownService

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class StatusLog(Log):
    """A log widget for status messages"""
    
    def on_mount(self) -> None:
        self.border_title = "Status Log"

class ScraperStatus(Static):
    """Status indicator with progress"""
    status = reactive("Ready")
    
    def compose(self) -> ComposeResult:
        yield LoadingIndicator()
        yield Label(self.status)
    
    def render(self) -> str:
        return self.status

class GeminiTUI(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #workspace {
        width: 90%;
        height: 90%;
        border: solid green;
        padding: 1;
    }

    .status {
        dock: bottom;
        padding: 1;
        background: $surface;
        color: $text;
    }

    Button {
        width: 30;
        margin: 1;
    }

    #controls {
        height: auto;
        align: center middle;
        padding: 1;
    }

    DataTable {
        height: 1fr;
        margin: 1;
    }

    LoadingIndicator {
        width: 1;
        height: 1;
    }

    #status_log {
        height: 30%;
        margin: 1;
        border: solid $primary;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "sync", "Sync to Val.Town", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.scraper = None
        self.status_widget = ScraperStatus()
        self.console = Console()
        self.valtown = ValTownService()
        self.status_log = StatusLog()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="workspace"):
            with Container(id="controls"):
                yield Button("Extract Tokens", id="extract", variant="primary")
                yield Button("Start Scraping", id="scrape", variant="success")
                yield Button("View Results", id="view", variant="warning")
                yield Button("Sync to Val.Town", id="sync", variant="primary")
            yield self.status_widget
            yield self.status_log
            yield DataTable(id="results")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Timestamp", "Content")
        self.status_log.write("[blue]System initialized and ready")

    @work
    async def extract_tokens(self):
        """Extract tokens with progress updates"""
        self.status_widget.status = "Extracting tokens..."
        self.status_log.write("[blue]Starting token extraction...")
        try:
            cookies = extract_google_cookies()
            if cookies:
                self.status_widget.status = "Tokens extracted!"
                self.status_log.write("[green]✓ Tokens extracted and saved to cookies.json")
                self.status_log.write("[green]✓ Auth token saved to .env")
            else:
                self.status_widget.status = "Token extraction failed"
                self.status_log.write("[red]✗ Failed to extract tokens")
        except Exception as e:
            self.status_widget.status = "Error"
            self.status_log.write(f"[red]✗ Error: {str(e)}")

    @work
    async def start_scraping(self):
        """Scrape conversations with progress updates"""
        self.status_widget.status = "Scraping..."
        self.status_log.write("[blue]Starting conversation scraping...")
        try:
            scraper = GeminiScraper(cookies_file="cookies.json")
            conversations = scraper.run()
            
            if conversations:
                # Update table with results
                table = self.query_one(DataTable)
                table.clear()
                for conv in conversations:
                    table.add_row(conv['timestamp'], conv['content'])
                
                self.status_widget.status = "Scraping completed!"
                self.status_log.write(f"[green]✓ Scraped {len(conversations)} conversations")
            else:
                self.status_widget.status = "No conversations found"
                self.status_log.write("[yellow]! No conversations were found")
        except Exception as e:
            self.status_widget.status = "Error"
            self.status_log.write(f"[red]✗ Error: {str(e)}")

    @work
    async def sync_to_valtown(self):
        """Sync conversations to Val.Town"""
        self.status_widget.status = "Syncing..."
        self.status_log.write("[blue]Starting Val.Town sync...")
        try:
            with open('gemini_conversations.json', 'r') as f:
                conversations = json.load(f)
            
            url = await self.valtown.store_conversations(conversations)
            self.status_widget.status = "Sync completed!"
            self.status_log.write(f"[green]✓ Synced to Val.Town")
            self.status_log.write(f"[blue]URL: {url}")
        except FileNotFoundError:
            self.status_widget.status = "No data to sync"
            self.status_log.write("[yellow]! No conversation data found to sync")
        except Exception as e:
            self.status_widget.status = "Sync failed"
            self.status_log.write(f"[red]✗ Error: {str(e)}")

    def action_sync(self):
        """Sync conversations to Val.Town"""
        self.sync_to_valtown()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "extract":
            self.extract_tokens()
        elif button_id == "scrape":
            self.start_scraping()
        elif button_id == "view":
            self.view_results()
        elif button_id == "sync":
            self.sync_to_valtown()

    def view_results(self):
        """View scraped results"""
        try:
            with open('gemini_conversations.json', 'r') as f:
                conversations = json.load(f)
                table = self.query_one(DataTable)
                table.clear()
                for conv in conversations:
                    table.add_row(conv['timestamp'], conv['content'])
            self.status_widget.status = "Results loaded"
            self.status_log.write(f"[green]✓ Loaded {len(conversations)} conversations")
        except FileNotFoundError:
            self.status_widget.status = "No results found"
            self.status_log.write("[yellow]! No results file found. Try scraping first.")
        except Exception as e:
            self.status_widget.status = "Error"
            self.status_log.write(f"[red]✗ Error: {str(e)}")

    def action_refresh(self):
        self.view_results()

if __name__ == "__main__":
    app = GeminiTUI()
    app.run()

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Button, Static, DataTable, Label, LoadingIndicator, Log
from textual.binding import Binding
from textual.reactive import reactive
from textual import work
from rich.console import Console
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from gemini_scraper import GeminiScraper

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
    ]

    def __init__(self):
        super().__init__()
        self.scraper = GeminiScraper()
        self.status_widget = ScraperStatus()
        self.console = Console()
        self.status_log = StatusLog()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="workspace"):
            with Container(id="controls"):
                yield Button("Start Scraping", id="scrape", variant="success")
                yield Button("View Results", id="view", variant="warning")
            yield self.status_widget
            yield self.status_log
            yield DataTable(id="results")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Timestamp", "Content")
        self.status_log.write("[blue]System initialized and ready")

    @work
    async def start_scraping(self):
        """Start the scraping process"""
        self.status_widget.status = "Scraping..."
        self.status_log.write("[blue]Starting conversation scraping...")
        
        try:
            conversations = await self.scraper.scrape(cookies_file="cookies.json")
            
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "scrape":
            self.start_scraping()
        elif button_id == "view":
            self.view_results()

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

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
import json
import traceback
import sys
from extract_token import extract_google_cookies
from gemini_scraper import GeminiScraper

app = typer.Typer()
console = Console()

def debug_info():
    """Print debug information"""
    console.print("[yellow]Debug Information:[/yellow]")
    console.print(f"Python version: {sys.version}")
    console.print(f"Current directory: {Path.cwd()}")
    try:
        import textual
        console.print(f"Textual version: {textual.__version__}")
    except Exception as e:
        console.print(f"[red]Error importing textual: {str(e)}[/red]")

@app.command()
def extract_tokens():
    """Extract Google authentication tokens from Chrome"""
    with console.status("[bold green]Extracting tokens...") as status:
        try:
            cookies = extract_google_cookies()
            if cookies:
                console.print("[bold green]✓ Tokens extracted successfully!")
            else:
                console.print("[bold red]✗ Failed to extract tokens")
        except Exception as e:
            console.print(f"[bold red]Error: {str(e)}")

@app.command()
def scrape(headless: bool = True):
    """Scrape Gemini conversations"""
    with console.status("[bold green]Scraping conversations...") as status:
        try:
            scraper = GeminiScraper(cookies_file="cookies.json")
            conversations = scraper.run()
            console.print(f"[bold green]✓ Scraped {len(conversations)} conversations!")
        except Exception as e:
            console.print(f"[bold red]Error: {str(e)}")

@app.command()
def view():
    """View scraped conversations"""
    try:
        with open('gemini_conversations.json', 'r') as f:
            conversations = json.load(f)
        
        table = Table(title="Gemini Conversations")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Content", style="green")
        
        for conv in conversations:
            table.add_row(conv['timestamp'], conv['content'])
        
        console.print(table)
        
    except FileNotFoundError:
        console.print("[bold red]No results file found")
    except Exception as e:
        console.print(f"[bold red]Error loading results: {str(e)}")

@app.command()
def interactive():
    """Launch the interactive TUI"""
    try:
        debug_info()  # Print debug information before starting
        from gemini_tui import GeminiTUI
        console.print("[green]Starting TUI...[/green]")
        app = GeminiTUI()
        app.run()
    except Exception as e:
        console.print("[bold red]Error starting TUI:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print("[yellow]Full traceback:[/yellow]")
        console.print(traceback.format_exc())

if __name__ == "__main__":
    app()

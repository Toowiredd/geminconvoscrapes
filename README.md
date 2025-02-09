# Gemini Conversation History Scraper

This tool allows you to scrape and save your Google Gemini conversation history from Google My Activity.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Authentication Options:

   a. Using Cookies (Recommended):
   - Export your Google cookies to a `cookies.json` file
   - Place the file in the project directory

   b. Manual Login:
   - The script will open a browser window for manual login
   - After successful login, the session will be maintained

## Usage

You can use this tool in three different ways:

### 1. Interactive TUI (Recommended)
Launch the Text User Interface:
```bash
python cli.py interactive
```

The TUI provides a user-friendly interface with:
- Token extraction
- Conversation scraping
- Real-time status updates
- Results viewing
- Keyboard shortcuts

### 2. Command Line Interface
Use the CLI for quick operations:

```bash
# Extract tokens
python cli.py extract-tokens

# Scrape conversations
python cli.py scrape

# View results
python cli.py view
```

### 3. Python API
Import and use the scraper in your code:

```python
from gemini_scraper import GeminiScraper

scraper = GeminiScraper(cookies_file="cookies.json")
scraper.run()
```

## Authentication

The tool supports two authentication methods:

1. **Automatic Token Extraction** (Recommended):
   - Uses browser-cookie3 to safely extract tokens from Chrome
   - Automatically creates necessary auth files

2. **Manual Token Configuration**:
   - Create a `.env` file from `.env.example`
   - Add your Google authentication token

## Output Format

The conversations are saved in JSON format:
```json
[
  {
    "timestamp": "Feb 9, 2024 2:30 PM",
    "content": "Conversation content here..."
  }
]
```

## Customization

- Modify the `gemini_scraper.py` script to adjust scraping parameters
- Enable headless mode by uncommenting the relevant line in `setup_driver()`
- Adjust wait times and selectors as needed

## Requirements

- Python 3.8+
- Chrome browser installed
- Internet connection
- Google account with Gemini history

## Keyboard Shortcuts (TUI)

- `q`: Quit the application
- `r`: Refresh the results view

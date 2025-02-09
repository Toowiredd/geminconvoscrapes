from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Button, Static, Label
from textual.binding import Binding

class SimpleApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    Container {
        width: 40;
        height: auto;
        border: solid green;
        padding: 1;
    }

    Button {
        width: 30;
        margin: 1;
    }

    Label {
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Label("Gemini Scraper")
            yield Button("Test Button", id="test")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "test":
            self.notify("Button works!")

if __name__ == "__main__":
    app = SimpleApp()
    app.run()

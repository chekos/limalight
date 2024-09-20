from .display_factory import get_display
import logging
import typer

app = typer.Typer()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Get the appropriate display
_display = get_display()


@app.command()
def display(message: str, duration: int = 5, return_to_idle: bool = False):
    _display.display_message(message, duration, return_to_idle)

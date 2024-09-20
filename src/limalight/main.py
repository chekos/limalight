import logging
from .display_factory import get_display

# Set up logging
logging.basicConfig(level=logging.INFO)

# Get the appropriate display
display = get_display()

# Use the display
display.display_message("Welcome to Limonada Journaling!", duration=5)
display.play_animation("idle", loop=True, fps=2)

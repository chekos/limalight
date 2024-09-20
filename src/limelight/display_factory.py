import platform
import logging
from .oled_display import OLEDDisplay, HARDWARE_AVAILABLE
from .terminal_display import TerminalDisplay


def get_display():
    OS_TYPE = platform.system()

    if OS_TYPE == "Linux" and HARDWARE_AVAILABLE:
        try:
            return OLEDDisplay()
        except Exception as e:
            logging.error(f"Error initializing OLEDDisplay: {e}")
            logging.info("Falling back to TerminalDisplay.")
            return TerminalDisplay()
    else:
        logging.info(
            "OLED hardware not available or not running on Linux. Using TerminalDisplay."
        )
        return TerminalDisplay()

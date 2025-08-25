import datetime
import sys
import time
import traceback
from colorama import Fore, Style, init

# Initialize Colorama for cross-platform compatibility
init()

class Logger:
    def __init__(self):
        pass

    def _get_timestamp(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def _log(self, level, message, color, stream=sys.stdout, prefix=""):
        timestamp = self._get_timestamp()
        print(f"{color}{Style.BRIGHT}[{timestamp}]{Style.RESET_ALL} {prefix}{message}{Style.RESET_ALL}", file=stream)

    def info(self, message):
        self._log("INFO", message, Fore.CYAN)

    def success(self, message):
        self._log("SUCCESS", message, Fore.GREEN, prefix=f"{Style.BRIGHT}✓ {Style.RESET_ALL}{Fore.GREEN}")

    def warning(self, message):
        self._log("WARNING", message, Fore.YELLOW, stream=sys.stderr, prefix=f"{Style.BRIGHT}⚠ {Style.RESET_ALL}{Fore.YELLOW}")

    def error(self, message):
        self._log("ERROR", message, Fore.RED, stream=sys.stderr, prefix=f"{Style.BRIGHT}✖ {Style.RESET_ALL}{Fore.RED}")

    def debug(self, message):
        self._log("DEBUG", message, Fore.WHITE + Style.DIM)

    def exception(self, exc_type, exc_value, exc_traceback):
        self.error(f"An unhandled exception occurred: {exc_value}")
        formatted_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for line in formatted_lines:
            for sub_line in line.splitlines():
                if sub_line.strip():
                    self._log("TRACEBACK", f">> {sub_line}", Fore.RED, stream=sys.stderr)

logger = Logger()

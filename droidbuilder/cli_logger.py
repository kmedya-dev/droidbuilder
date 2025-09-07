import datetime
import sys
import time
import traceback
import os
import shutil
from colorama import Fore, Style, init

# Initialize Colorama
init(autoreset=True)

LOG_DIR = os.path.join(os.path.expanduser("~"), ".droidbuilder", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

class Logger:
    def __init__(self):
        self.log_file = os.path.join(
            LOG_DIR,
            f"droidbuilder_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

    def _get_timestamp(self):
        return datetime.datetime.now().strftime("%H:%M:%S")

    def _log(self, level, message, color, stream=sys.stdout, prefix="", show_timestamp=True):
        if show_timestamp:
            timestamp = self._get_timestamp()
            log_message = f"[{timestamp}] [{level}] {prefix}{message}\n"
            print(f"{color}{Style.BRIGHT}[{timestamp}]{Style.RESET_ALL} {prefix}{message}{Style.RESET_ALL}", file=stream)
        else:
            log_message = f"[{level}] {prefix}{message}\n"
            print(f"{color}{prefix}{message}{Style.RESET_ALL}", file=stream)

        with open(self.log_file, "a") as f:
            f.write(log_message)

    def info(self, message):
        self._log("INFO", message, Fore.CYAN)

    def step_info(self, message, indent=0):
        prefix = " " * indent
        self._log("", message, Fore.CYAN, prefix=prefix, show_timestamp=False)

    def success(self, message):
        self._log("SUCCESS", message, Fore.GREEN, prefix=f"{Style.BRIGHT}✓ {Style.RESET_ALL}{Fore.GREEN}")

    def warning(self, message):
        self._log("WARNING", message, Fore.YELLOW, stream=sys.stderr,
                  prefix=f"{Style.BRIGHT}⚠ {Style.RESET_ALL}{Fore.YELLOW}")

    def error(self, message):
        self._log("ERROR", message, Fore.RED, stream=sys.stderr,
                  prefix=f"{Style.BRIGHT}✖ {Style.RESET_ALL}{Fore.RED}")

    def debug(self, message):
        self._log("DEBUG", message, Fore.WHITE + Style.DIM)

    # -------- Progress bar method --------
    def progress(self, iterable, description="Downloading", total=None, bar_length=30, unit="b"):
        if total is None:
            try:
                total = len(iterable)
            except TypeError:
                for item in iterable:
                    yield item
                return

        start_time = time.time()
        current_val = 0
        is_bytes = (unit.lower() == 'b')

        def format_size(bytes_val):
            if bytes_val >= 1024 * 1024 * 1024:
                return f"{bytes_val / (1024*1024*1024):.1f} GB"
            if bytes_val >= 1024 * 1024:
                return f"{bytes_val / (1024*1024):.1f} MB"
            if bytes_val >= 1024:
                return f"{bytes_val / 1024:.1f} KB"
            return f"{int(bytes_val)} B"

        print(f"{description}...")
        print()
        sys.stdout.flush()

        for i, item in enumerate(iterable):
            yield item

            # Current progress
            if is_bytes:
                try:
                    current_val += len(item)
                except TypeError:
                    current_val += 1
            else:
                current_val = i + 1

            elapsed = time.time() - start_time
            percent = min(1.0, current_val / total if total > 0 else 0)
            filled_len = int(bar_length * percent)

            # Bar
            bar = Fore.GREEN + "━" * filled_len
            if filled_len < bar_length:
                bar += Fore.RED + "╺" + Style.RESET_ALL + "━" * (bar_length - filled_len - 1)
            else:
                bar += Style.RESET_ALL

            speed = current_val / elapsed if elapsed > 0 else 0
            remaining = total - current_val
            eta = remaining / speed if speed > 0 else 0

            if is_bytes:
                speed_unit, speed_divisor = ("MB/s", 1024*1024)
                if speed > 1024*1024*1024:
                    speed_unit, speed_divisor = ("GB/s", 1024*1024*1024)
            else:
                speed_unit, speed_divisor = ("it/s", 1)

            line = (
                f"{percent*100:3.0f}% | "
                f"{bar} | "
                f"{format_size(current_val)}/{format_size(total)} • "
                f"{speed/speed_divisor:.1f} {speed_unit} • "
                f"{time.strftime('%M:%S', time.gmtime(elapsed))}/"
                f"{time.strftime('%M:%S', time.gmtime(elapsed+eta))}"
            )

        # Overwrite same line
        terminal_width = shutil.get_terminal_size().columns
        if terminal_width < len(line):
            # for small display
            sys.stdout.write("\x1b[F\x1b[F\r")
            print(line)
        else:
            # for large display
            sys.stdout.write("\x1b[F\r")
            print(line)
        sys.stdout.flush()

        # completion message
        print("\n✅ Download complete!")

    # -------- Exception logging --------
    def exception(self, exc_type, exc_value, exc_traceback):
        self.error(f"An unhandled exception occurred: {exc_value}")
        formatted_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for line in formatted_lines:
            for sub_line in line.splitlines():
                if sub_line.strip():
                    self._log("TRACEBACK", f">> {sub_line}", Fore.RED, stream=sys.stderr)


# ---------------- Helper ----------------
logger = Logger()

def get_latest_log_file():
    """Return the path to the latest log file."""
    log_files = [os.path.join(LOG_DIR, f) for f in os.listdir(LOG_DIR) if f.endswith(".log")]
    if not log_files:
        return None
    return max(log_files, key=os.path.getctime)

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

    def _log(self, level, message, color, stream=sys.stdout, prefix="", show_timestamp=True):
        if show_timestamp:
            timestamp = self._get_timestamp()
            print(f"{color}{Style.BRIGHT}[{timestamp}]{Style.RESET_ALL} {prefix}{message}{Style.RESET_ALL}", file=stream)
        else:
            print(f"{color}{prefix}{message}{Style.RESET_ALL}", file=stream)

    def info(self, message):
        self._log("INFO", message, Fore.CYAN)

    def step_info(self, message, indent=0):
        prefix = " " * indent
        self._log("", message, Fore.CYAN, prefix=prefix, show_timestamp=False)

    def success(self, message):
        self._log("SUCCESS", message, Fore.GREEN, prefix=f"{Style.BRIGHT}✓ {Style.RESET_ALL}{Fore.GREEN}")

    def warning(self, message):
        self._log("WARNING", message, Fore.YELLOW, stream=sys.stderr, prefix=f"{Style.BRIGHT}⚠ {Style.RESET_ALL}{Fore.YELLOW}")

    def error(self, message):
        self._log("ERROR", message, Fore.RED, stream=sys.stderr, prefix=f"{Style.BRIGHT}✖ {Style.RESET_ALL}{Fore.RED}")

    def debug(self, message):
        self._log("DEBUG", message, Fore.WHITE + Style.DIM)

    def progress(self, iterable, description="", total=None, bar_length=30, unit="it"):
        if total is None:
            try:
                total = len(iterable)
            except TypeError:
                for item in iterable:
                    yield item
                return

        start_time = time.time()

        def format_size(bytes_val):
            if bytes_val >= 1024 * 1024 * 1024:
                return f"{bytes_val / (1024*1024*1024):.1f} GB"
            if bytes_val >= 1024 * 1024:
                return f"{bytes_val / (1024*1024):.1f} MB"
            if bytes_val >= 1024:
                return f"{bytes_val / 1024:.1f} KB"
            return f"{int(bytes_val)} B"

        # Reserve space and hide cursor
        sys.stdout.write("\n\n\n")
        sys.stdout.write("\x1b[?25l")
        sys.stdout.flush()

        current_val = 0
        is_bytes = (unit.lower() == 'b')

        for i, item in enumerate(iterable):
            yield item

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

            # Bar building
            bar = Fore.GREEN + "━" * filled_len
            if filled_len < bar_length:
                bar += Style.RESET_ALL + Fore.RED + "╺" + Style.RESET_ALL
                bar += "━" * (bar_length - filled_len - 1)
            else:
                bar += Style.RESET_ALL

            speed = current_val / elapsed if elapsed > 0 else 0
            remaining = total - current_val
            eta = remaining / speed if speed > 0 else 0

            # Move cursor up
            sys.stdout.write("\x1b[F\x1b[F\x1b[F")

            line1 = f"{Fore.GREEN}{description}{Style.RESET_ALL}   "
            line2 = f"{bar} {percent*100:3.0f}%   "

            if is_bytes:
                speed_unit, speed_divisor = ("MB/s", 1024*1024)
                if speed > 1024*1024*1024:
                    speed_unit, speed_divisor = ("GB/s", 1024*1024*1024)
                
                line3 = (f"{format_size(current_val)}/{format_size(total)} • {speed/speed_divisor:.1f} {speed_unit} • "
                         f"{time.strftime('%M:%S', time.gmtime(elapsed))}/"
                         f"{time.strftime('%M:%S', time.gmtime(elapsed+eta))}   ")
            else:
                line3 = (
                    f"{current_val}/{total} • {speed:.1f} it/s • "
                    f"{time.strftime('%M:%S', time.gmtime(elapsed))}/"
                    f"{time.strftime('%M:%S', time.gmtime(elapsed+eta))}   "
                )

            print(line1)
            print(line2)
            print(line3)
            sys.stdout.flush()

        # Show cursor again and move to the next line
        sys.stdout.write("\x1b[?25h")
        sys.stdout.write("\n\n\n")
        sys.stdout.flush()
        self.success(f"{description} complete!")

    def exception(self, exc_type, exc_value, exc_traceback):
        self.error(f"An unhandled exception occurred: {exc_value}")
        formatted_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for line in formatted_lines:
            for sub_line in line.splitlines():
                if sub_line.strip():
                    self._log("TRACEBACK", f">> {sub_line}", Fore.RED, stream=sys.stderr)

logger = Logger()
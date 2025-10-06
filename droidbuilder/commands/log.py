import click
import sys
import traceback
import os
from ..cli_logger import get_latest_log_file, LOG_DIR
from colorama import Fore, Style

@click.command()
@click.option('--filename', default=None, help='The name of the log file to display.')
@click.option('--list', 'list_files', is_flag=True, help='List all log files.')
def log(filename, list_files):
    """Display a specific log file or the latest log file, or list all log files."""
    if list_files:
        if not os.path.exists(LOG_DIR):
            sys.stdout.write("Log directory does not exist.")
            return
        log_files = [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]
        if not log_files:
            sys.stdout.write("No log files found.")
            return
        sys.stdout.write("Available log files:")
        for f in sorted(log_files):
            print(f"  {f}")
        return

    log_file = None
    if filename:
        log_file = os.path.join(LOG_DIR, filename)
    else:
        log_file = get_latest_log_file()

    if not log_file or not os.path.exists(log_file):
        sys.stdout.write("No log files found.")
        return

    sys.stdout.write(f"Displaying log file: {log_file}")
    try:
        with open(log_file, 'r') as f:
            for line in f:
                color = Fore.CYAN # Default to cyan
                if "[WARNING]" in line:
                    color = Fore.YELLOW
                elif "[ERROR]" in line:
                    color = Fore.RED
                elif "[DEBUG]" in line:
                    color = Fore.WHITE + Style.DIM
                elif "[SUCCESS]" in line:
                    color = Fore.GREEN
                elif "[TRACEBACK]" in line:
                    color = Fore.RED
                elif "[INFO]" in line:
                    color = Fore.CYAN
                print(f"{color}{line.strip()}{Style.RESET_ALL}")
    except IOError as e:
        sys.stderr.write(f"Error reading log file {log_file}: {e}")
        sys.stdout.write("Please check file permissions.")
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred while reading log file {log_file}: {e}")
        traceback.print_exc(file=sys.stderr)

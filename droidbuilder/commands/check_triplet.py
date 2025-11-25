"""
Check Triplet Command
---------------------

This command determines and prints the system triplet, which is a string that
identifies the system's architecture, vendor, OS, and C library.
The format of the triplet is: arch-vendor-system-libc.
"""

import click
from ..cli_logger import logger
from ..utils import get_triplet

@click.command("check-triplet")
def check_triplet():
    """
    Constructs and prints the system triplet.
    """
    triplet = get_triplet()
    logger.info(f"System triplet: {triplet}")


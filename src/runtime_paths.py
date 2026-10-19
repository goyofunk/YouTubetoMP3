"""Paths shared by source execution and the self-contained Windows bundle."""
from pathlib import Path
import sys

RESOURCE_DIR = Path(__file__).resolve().parent


def application_directory():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return RESOURCE_DIR


TOOLS_DIR = (application_directory() if getattr(sys, 'frozen', False) else RESOURCE_DIR.parent) / 'tools'

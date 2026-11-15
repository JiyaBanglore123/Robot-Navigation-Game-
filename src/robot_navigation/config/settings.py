"""
Application configuration settings.
Configures file paths, network settings, and input mapping.
"""

import os
from pathlib import Path

# Base project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

ASSETS_DIR = BASE_DIR / "assets"
STATE_CONFIG_PATH = ASSETS_DIR / "state_config.yaml"

# Network settings
HOST = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
PORT = int(os.environ.get("FLASK_RUN_PORT", 5000))
DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

# Secret key for Flask application session security
SECRET_KEY = os.environ.get("SECRET_KEY", "dfa-robot-navigation-secret-key-university-fla")

# Mapping frontend direction inputs to DFA movement symbols
# Supported frontend directions: UP, DOWN, LEFT, RIGHT
DIRECTION_MAPPING = {
    "UP": "U",
    "DOWN": "D",
    "LEFT": "L",
    "RIGHT": "R"
}

VALID_DIRECTIONS = set(DIRECTION_MAPPING.keys())

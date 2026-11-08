#!/usr/bin/env python3
"""
Convenience entry point for running the Flask server.
"""
import sys
from pathlib import Path

# Add src to sys.path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from robot_navigation.app import app, create_app
from robot_navigation.config.settings import DEBUG, HOST, PORT

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)

#!/usr/bin/env bash
# ==============================================================================
# Robot Navigation Game — Linux/Ubuntu Execution Script
# Author: Ankur (Person 2)
# ==============================================================================

set -euo pipefail

# 1. Detect and move to project root directory regardless of current working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo " Starting DFA-Based Robot Navigation Game (FLA Project) "
echo " Working directory: $SCRIPT_DIR"
echo "=========================================================="

# 2. Check Python 3 installation
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 could not be found. Please install Python 3.10+." >&2
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "[1/5] Detected Python: $PYTHON_VERSION"

# 3. Check or create virtual environment
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "[2/5] Creating Python virtual environment in .venv..."
    python3 -m venv "$VENV_DIR"
else
    echo "[2/5] Existing virtual environment found in .venv."
fi

# 4. Activate virtual environment
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 5. Upgrade pip and install required dependencies
echo "[3/5] Upgrading pip..."
python -m pip install --upgrade pip --quiet

echo "[4/5] Checking and installing dependencies from requirements.txt..."
python -m pip install -r requirements.txt --quiet

# 6. Configure Host & Port
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-5000}"

echo "[5/5] Launching Flask Server..."
echo "=========================================================="
echo " Application running at: http://$HOST:$PORT"
echo " Press Ctrl+C to stop the application server."
echo "=========================================================="

# 7. Start the Flask application
exec python -m flask --app app run --host "$HOST" --port "$PORT"

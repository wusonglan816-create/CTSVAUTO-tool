#!/bin/bash
set -e

echo "=== CTS Verifier automation setup ==="

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo "Python 3.10+ is required. Current: $PYTHON_VERSION"
    exit 1
fi

if ! command -v adb >/dev/null 2>&1; then
    echo "ADB is required. Install with: sudo apt-get install android-tools-adb"
    exit 1
fi

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

echo "Setup complete. Run: cts-verify quickstart"

#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="${VENV_DIR:-.venv}"
export PIP_REQUIRE_VIRTUALENV=true

# Ensure venv exists
if [ ! -d "$VENV_DIR" ]; then
	python3 -m venv "$VENV_DIR" || {
		echo "Failed to create virtualenv at $VENV_DIR. Please install python3-venv and retry." >&2
		exit 1
	}
fi

# Activate venv and install deps strictly inside it
. "$VENV_DIR/bin/activate"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r requirements.txt

# Start aria2 and the bot using venv python
./aria.sh
exec "$VENV_DIR/bin/python" -m bot
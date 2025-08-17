#!/usr/bin/env bash
set -e

VENV_DIR="${VENV_DIR:-.venv}"

use_venv=false
if [ -d "$VENV_DIR" ]; then
	use_venv=true
elif python3 -c "import venv" >/dev/null 2>&1; then
	use_venv=true
fi

if [ "$use_venv" = true ]; then
	if [ ! -d "$VENV_DIR" ]; then
		python3 -m venv "$VENV_DIR"
	fi
	. "$VENV_DIR/bin/activate"
	pip install --upgrade pip
	pip install -r requirements.txt
fi

./aria.sh
python -m bot
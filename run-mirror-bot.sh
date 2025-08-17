#!/usr/bin/env bash
set -euo pipefail

# Always operate from the directory containing this script (expected repo root)
cd "$(dirname "$0")"

# Preflight checks
if ! command -v sudo >/dev/null 2>&1; then
  echo "Error: 'sudo' command not found. Please install sudo or run this script as root." >&2
  exit 127
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "Error: 'docker' CLI not found. Please install Docker Engine (client + daemon)." >&2
  echo "Hint (Ubuntu/Debian): sudo apt-get update && sudo apt-get install -y docker.io" >&2
  exit 127
fi
if ! command -v dockerd >/dev/null 2>&1; then
  echo "Error: 'dockerd' daemon not found. Please install Docker Engine." >&2
  exit 127
fi

# Start Docker daemon if not running
if pgrep -x dockerd >/dev/null 2>&1; then
  echo "Docker daemon is already running."
else
  echo "Starting Docker daemon..."
  sudo dockerd >/dev/null 2>&1 &
  # Wait until Docker is ready (timeout ~30s)
  ready=false
  for i in {1..30}; do
    if sudo -n docker info >/dev/null 2>&1; then
      ready=true
      echo "Docker daemon is ready."
      break
    fi
    sleep 1
  done
  if [ "$ready" != true ]; then
    echo "Warning: Timed out waiting for Docker daemon to become ready. Continuing anyway..." >&2
  fi
fi

# Build Docker image
echo "Building Docker image 'mirror-bot'..."
sudo -n docker build . -t mirror-bot

# Run the image
echo "Running Docker image 'mirror-bot'..."
sudo -n docker run mirror-bot
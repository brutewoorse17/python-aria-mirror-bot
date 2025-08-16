#!/bin/bash

# Mega.nz Link Downloader using JDownloader
# Usage: ./download_mega.sh "mega.nz link1" "mega.nz link2" ...

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

# Check if required Python packages are installed
python3 -c "import requests" 2>/dev/null || {
    echo -e "${YELLOW}Installing required Python packages...${NC}"
    pip3 install requests
}

# Check if config file exists
if [ ! -f "config.json" ]; then
    echo -e "${RED}Error: config.json not found. Please create it first.${NC}"
    echo "Copy config.json.example and fill in your MyJDownloader credentials."
    exit 1
fi

# Check if links are provided
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage: $0 \"mega.nz link1\" \"mega.nz link2\" ...${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 \"https://mega.nz/file/example\""
    echo "  $0 \"https://mega.nz/folder/example\" \"https://mega.nz/file/example2\""
    echo ""
    echo "Make sure to:"
    echo "1. Have JDownloader installed and running"
    echo "2. Have a MyJDownloader account"
    echo "3. Configure config.json with your credentials"
    exit 1
fi

# Extract email and password from config
EMAIL=$(python3 -c "import json; print(json.load(open('config.json'))['jdownloader']['email'])")
PASSWORD=$(python3 -c "import json; print(json.load(open('config.json'))['jdownloader']['password'])")
DEVICE_NAME=$(python3 -c "import json; print(json.load(open('config.json')).get('jdownloader', {}).get('device_name', ''))")

# Check if credentials are configured
if [ "$EMAIL" = "your_email@example.com" ] || [ "$PASSWORD" = "your_password" ]; then
    echo -e "${RED}Error: Please configure your MyJDownloader credentials in config.json${NC}"
    exit 1
fi

echo -e "${GREEN}Starting Mega.nz download process...${NC}"
echo "Email: $EMAIL"
echo "Device: ${DEVICE_NAME:-'Auto-detected'}"
echo "Links: $#"
echo ""

# Build command
CMD="python3 mega_jdownloader_api.py"
if [ -n "$DEVICE_NAME" ]; then
    CMD="$CMD --device-name \"$DEVICE_NAME\""
fi
CMD="$CMD --email \"$EMAIL\" --password \"$PASSWORD\""

# Add links
for link in "$@"; do
    CMD="$CMD \"$link\""
done

# Add monitoring
CMD="$CMD --monitor --monitor-interval 30"

echo -e "${YELLOW}Executing: $CMD${NC}"
echo ""

# Execute the download
eval $CMD

echo ""
echo -e "${GREEN}Download process completed!${NC}"
echo "Check JDownloader for download progress and status."
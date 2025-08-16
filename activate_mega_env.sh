#!/bin/bash
# Script to activate MEGA virtual environment and verify installation

echo "Activating MEGA virtual environment..."
source venv/bin/activate

echo "Checking MEGA packages installation..."
pip list | grep -i mega

echo ""
echo "Testing MEGA packages..."
python3 async_mega_example.py

echo ""
echo "Virtual environment is now active!"
echo "Use 'deactivate' to exit the virtual environment"
echo ""
echo "Available MEGA packages:"
echo "- megasdkrestclient: For programmatic use (async context)"
echo "- mega: For terminal-based operations"
echo ""
echo "See MEGA_INSTALLATION_README.md for detailed usage instructions"
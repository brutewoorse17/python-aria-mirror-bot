#!/usr/bin/env python3
"""
Test script for Mega.nz JDownloader bot integration
This script tests the core functionality without running the full bot
"""

import os
import sys
import json
import asyncio
from unittest.mock import Mock, patch

# Add bot directory to path
sys.path.append('bot')

def test_config_loading():
    """Test configuration loading"""
    print("🧪 Testing configuration loading...")
    
    # Test config.json loading
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            required_keys = ['email', 'password']
            for key in required_keys:
                if key not in config.get('jdownloader', {}):
                    print(f"❌ Missing required key: {key}")
                    return False
                if config['jdownloader'][key] in ['your_email@example.com', 'your_password']:
                    print(f"⚠️  Please update {key} in config.json")
                    return False
            
            print("✅ Configuration loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return False
    else:
        print("⚠️  config.json not found - please create it first")
        return False

def test_mega_jdownloader_api():
    """Test Mega.nz JDownloader API functionality"""
    print("\n🧪 Testing Mega.nz JDownloader API...")
    
    try:
        from mega_jdownloader_api import MegaJDownloaderAPI, JDownloaderConfig
        
        # Test configuration class
        config = JDownloaderConfig(
            email="test@example.com",
            password="test_password"
        )
        print("✅ JDownloaderConfig created successfully")
        
        # Test link validation
        from mega_jdownloader_api import MegaJDownloaderAPI
        downloader = MegaJDownloaderAPI(config)
        
        # Test valid links
        valid_links = [
            "https://mega.nz/file/example123",
            "https://mega.nz/folder/folder123",
            "https://mega.co.nz/file/example456"
        ]
        
        for link in valid_links:
            if downloader._is_valid_mega_link(link):
                print(f"✅ Valid link: {link}")
            else:
                print(f"❌ Invalid link: {link}")
                return False
        
        # Test invalid links
        invalid_links = [
            "https://example.com/file",
            "https://mega.nz/invalid/path",
            "not_a_url"
        ]
        
        for link in invalid_links:
            if not downloader._is_valid_mega_link(link):
                print(f"✅ Invalid link correctly rejected: {link}")
            else:
                print(f"❌ Invalid link incorrectly accepted: {link}")
                return False
        
        print("✅ Mega.nz JDownloader API tests passed")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_bot_modules():
    """Test bot module imports"""
    print("\n🧪 Testing bot module imports...")
    
    try:
        # Test core bot imports
        from bot.helper.telegram_helper.bot_commands import BotCommands
        print("✅ BotCommands imported successfully")
        
        # Test new commands
        if hasattr(BotCommands, 'MegaJDownloaderCommand'):
            print("✅ MegaJDownloaderCommand found")
        else:
            print("❌ MegaJDownloaderCommand not found")
            return False
            
        if hasattr(BotCommands, 'MegaJDownloaderStatusCommand'):
            print("✅ MegaJDownloaderStatusCommand found")
        else:
            print("❌ MegaJDownloaderStatusCommand not found")
            return False
        
        print("✅ Bot module tests passed")
        return True
        
    except ImportError as e:
        print(f"❌ Bot module import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Bot module test error: {e}")
        return False

def test_help_messages():
    """Test help message loading"""
    print("\n🧪 Testing help message loading...")
    
    try:
        from bot.helper.telegram_helper.help_messages import (
            MEGA_JD_HELP, BOT_HELP, COMMAND_EXAMPLES
        )
        
        # Check if help messages contain expected content
        if "Mega.nz JDownloader" in MEGA_JD_HELP:
            print("✅ MEGA_JD_HELP loaded with correct content")
        else:
            print("❌ MEGA_JD_HELP missing expected content")
            return False
            
        if "/megajd" in BOT_HELP:
            print("✅ BOT_HELP includes Mega.nz commands")
        else:
            print("❌ BOT_HELP missing Mega.nz commands")
            return False
            
        if "examples" in COMMAND_EXAMPLES:
            print("✅ COMMAND_EXAMPLES loaded successfully")
        else:
            print("❌ COMMAND_EXAMPLES missing expected content")
            return False
        
        print("✅ Help message tests passed")
        return True
        
    except ImportError as e:
        print(f"❌ Help message import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Help message test error: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n🧪 Testing dependencies...")
    
    try:
        import requests
        print("✅ requests library available")
        
        import urllib3
        print("✅ urllib3 library available")
        
        # Check if requirements file exists
        if os.path.exists('requirements-mega.txt'):
            print("✅ requirements-mega.txt found")
        else:
            print("⚠️  requirements-mega.txt not found")
        
        print("✅ Dependency tests passed")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Mega.nz JDownloader Bot Integration Test")
    print("=" * 50)
    
    tests = [
        test_dependencies,
        test_config_loading,
        test_mega_jdownloader_api,
        test_bot_modules,
        test_help_messages
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Integration is ready.")
        print("\n📋 Next steps:")
        print("1. Update config.json with your MyJDownloader credentials")
        print("2. Ensure JDownloader is running on your system")
        print("3. Start your bot with: python3 bot/__main__.py")
        print("4. Test with: /megajd <mega_link>")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Install missing dependencies: pip3 install -r requirements-mega.txt")
        print("2. Create config.json with your credentials")
        print("3. Check file permissions and paths")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
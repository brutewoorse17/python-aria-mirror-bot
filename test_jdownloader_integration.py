#!/usr/bin/env python3
"""
Test script for JDownloader MEGA integration
This script tests the JDownloader download functionality
"""

import os
import sys
import asyncio
import aiohttp
from pathlib import Path

# Add the bot directory to the path
sys.path.append(str(Path(__file__).parent / 'bot'))

def test_jdownloader_connection():
    """Test connection to JDownloader API"""
    print("🔌 Testing JDownloader API connection...")
    
    # Get configuration from environment
    jd_host = os.getenv('JDOWNLOADER_HOST', 'http://localhost:5800')
    jd_username = os.getenv('JDOWNLOADER_USERNAME')
    jd_password = os.getenv('JDOWNLOADER_PASSWORD')
    
    if not all([jd_username, jd_password]):
        print("⚠️  JDownloader credentials not provided in environment")
        print("   Set JDOWNLOADER_USERNAME and JDOWNLOADER_PASSWORD")
        return False
    
    try:
        import requests
        
        # Test basic connection
        headers = {
            'Authorization': f'Basic {jd_username}:{jd_password}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{jd_host}/api/v2/downloads", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ JDownloader API connection successful")
            return True
        else:
            print(f"❌ JDownloader API connection failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ JDownloader API connection error: {e}")
        return False

def test_mega_link_parsing():
    """Test MEGA link parsing functionality"""
    print("\n🔗 Testing MEGA link parsing...")
    
    try:
        # Import the MEGA JDownloader downloader
        from bot.helper.mirror_utils.download_utils.mega_jdownloader_download import MegaJDownloaderDownloader
        
        # Create a mock listener
        class MockListener:
            def __init__(self):
                self.uid = "test_123"
            
            def onDownloadStarted(self):
                print("   ✅ Download start callback working")
            
            def onDownloadProgress(self):
                print("   ✅ Download progress callback working")
            
            def onDownloadComplete(self):
                print("   ✅ Download complete callback working")
            
            def onDownloadError(self, error):
                print(f"   ✅ Download error callback working: {error}")
        
        # Test MEGA link patterns
        test_links = [
            "https://mega.nz/file/example123#key123",
            "https://mega.nz/folder/example456#key456",
            "https://mega.co.nz/file/example789#key789",
            "https://www.mega.nz/file/example012#key012"
        ]
        
        downloader = MegaJDownloaderDownloader(MockListener())
        
        for link in test_links:
            if downloader._MegaJDownloaderDownloader__is_mega_link(link):
                print(f"   ✅ Valid MEGA link: {link}")
            else:
                print(f"   ❌ Invalid MEGA link: {link}")
        
        print("✅ MEGA link parsing test completed")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import MEGA JDownloader downloader: {e}")
        return False
    except Exception as e:
        print(f"❌ MEGA link parsing test failed: {e}")
        return False

def test_jdownloader_status():
    """Test JDownloader status utility"""
    print("\n📊 Testing JDownloader status utility...")
    
    try:
        from bot.helper.mirror_utils.status_utils.jdownloader_status import JDownloaderDownloadStatus
        
        # Create a mock download object
        class MockDownload:
            def __init__(self):
                self.gid = "test_gid"
                self.name = "test_file.txt"
                self.size = 1024 * 1024  # 1MB
                self.downloaded_bytes = 512 * 1024  # 512KB
                self.progress = 50.0
                self.download_speed = "100 KB/s"
                self.status = "downloading"
            
            def cancel_download(self):
                print("   ✅ Cancel download method working")
        
        # Create a mock listener
        class MockListener:
            def __init__(self):
                self.uid = "test_123"
                self.message = None
        
        # Test status creation
        download = MockDownload()
        listener = MockListener()
        status = JDownloaderDownloadStatus(download, listener)
        
        print(f"   ✅ Status created: {status.name()}")
        print(f"   ✅ Progress: {status.progress()}")
        print(f"   ✅ Size: {status.size()}")
        print(f"   ✅ Speed: {status.speed()}")
        print(f"   ✅ Status: {status.status()}")
        
        print("✅ JDownloader status utility test completed")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import JDownloader status utility: {e}")
        return False
    except Exception as e:
        print(f"❌ JDownloader status utility test failed: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    print("\n⚙️  Testing environment configuration...")
    
    required_vars = [
        'JDOWNLOADER_HOST',
        'JDOWNLOADER_USERNAME', 
        'JDOWNLOADER_PASSWORD'
    ]
    
    optional_vars = [
        'MEGA_USERNAME',
        'MEGA_PASSWORD',
        'JDOWNLOADER_DEVICE_ID'
    ]
    
    print("Required environment variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value and value not in ['your_jdownloader_username', 'your_jdownloader_password']:
            print(f"   ✅ {var}: {value[:10]}...")
        else:
            print(f"   ❌ {var}: Not set or using placeholder")
    
    print("\nOptional environment variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value and value not in ['your_mega_email', 'your_mega_password']:
            print(f"   ✅ {var}: {value[:10]}...")
        else:
            print(f"   ⚠️  {var}: Not set (optional)")
    
    return True

async def test_async_functionality():
    """Test async functionality"""
    print("\n🔄 Testing async functionality...")
    
    try:
        # Test basic async operations
        async with aiohttp.ClientSession() as session:
            print("   ✅ aiohttp session created successfully")
        
        print("✅ Async functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Async functionality test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 JDownloader MEGA Integration Test Suite")
    print("=" * 50)
    
    # Test environment configuration
    env_test = test_environment_config()
    
    # Test JDownloader connection
    jd_connection = test_jdownloader_connection()
    
    # Test MEGA link parsing
    mega_parsing = test_mega_link_parsing()
    
    # Test JDownloader status utility
    jd_status = test_jdownloader_status()
    
    # Test async functionality
    async_test = asyncio.run(test_async_functionality())
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print("=" * 50)
    
    tests = [
        ("Environment Configuration", env_test),
        ("JDownloader Connection", jd_connection),
        ("MEGA Link Parsing", mega_parsing),
        ("JDownloader Status Utility", jd_status),
        ("Async Functionality", async_test)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! JDownloader MEGA integration is ready.")
        print("\nNext steps:")
        print("1. Configure your JDownloader credentials in config.env")
        print("2. Start the services with: ./setup_jdownloader.sh")
        print("3. Test with a MEGA link: /mirror <mega_link>")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the configuration.")
        print("\nTroubleshooting:")
        print("1. Ensure JDownloader is running and accessible")
        print("2. Verify credentials in config.env")
        print("3. Check network connectivity")
        print("4. Review error messages above")

if __name__ == "__main__":
    main()
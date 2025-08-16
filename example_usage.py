#!/usr/bin/env python3
"""
Example usage of Mega.nz JDownloader integration
This script demonstrates various ways to use the downloader
"""

from mega_jdownloader_api import MegaJDownloaderAPI, JDownloaderConfig
import json
import os

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            config_data = json.load(f)
        
        return JDownloaderConfig(
            email=config_data['jdownloader']['email'],
            password=config_data['jdownloader']['password'],
            device_name=config_data['jdownloader'].get('device_name'),
            api_url=config_data['jdownloader'].get('api_url', 'https://api.jdownloader.org')
        )
    except FileNotFoundError:
        print("Error: config.json not found. Please create it first.")
        return None
    except KeyError as e:
        print(f"Error: Missing required configuration key: {e}")
        return None

def example_single_download():
    """Example: Download a single Mega.nz file"""
    print("=== Single File Download Example ===")
    
    config = load_config()
    if not config:
        return
    
    downloader = MegaJDownloaderAPI(config)
    
    # Example Mega.nz link (replace with actual link)
    mega_link = "https://mega.nz/file/example123"
    
    print(f"Downloading: {mega_link}")
    success = downloader.download_mega_links([mega_link])
    
    if success:
        print("✅ Download started successfully!")
    else:
        print("❌ Failed to start download")

def example_multiple_downloads():
    """Example: Download multiple Mega.nz files"""
    print("\n=== Multiple Files Download Example ===")
    
    config = load_config()
    if not config:
        return
    
    downloader = MegaJDownloaderAPI(config)
    
    # Example Mega.nz links (replace with actual links)
    mega_links = [
        "https://mega.nz/file/file1",
        "https://mega.nz/file/file2",
        "https://mega.nz/folder/folder1"
    ]
    
    print(f"Downloading {len(mega_links)} links:")
    for link in mega_links:
        print(f"  - {link}")
    
    success = downloader.download_mega_links(mega_links, "/downloads")
    
    if success:
        print("✅ All downloads started successfully!")
    else:
        print("❌ Failed to start downloads")

def example_with_monitoring():
    """Example: Download with progress monitoring"""
    print("\n=== Download with Monitoring Example ===")
    
    config = load_config()
    if not config:
        return
    
    downloader = MegaJDownloaderAPI(config)
    
    mega_link = "https://mega.nz/file/example123"
    print(f"Downloading with monitoring: {mega_link}")
    
    # Start download
    success = downloader.download_mega_links([mega_link])
    
    if success:
        print("✅ Download started! Starting monitoring...")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            # Monitor progress (check every 30 seconds)
            downloader.monitor_progress(interval=30)
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
    else:
        print("❌ Failed to start download")

def example_custom_download_folder():
    """Example: Download to custom folder"""
    print("\n=== Custom Download Folder Example ===")
    
    config = load_config()
    if not config:
        return
    
    downloader = MegaJDownloaderAPI(config)
    
    mega_link = "https://mega.nz/file/example123"
    custom_folder = "/custom/downloads"
    
    print(f"Downloading to custom folder: {custom_folder}")
    print(f"Link: {mega_link}")
    
    success = downloader.download_mega_links([mega_link], custom_folder)
    
    if success:
        print("✅ Download started to custom folder!")
    else:
        print("❌ Failed to start download")

def example_batch_from_file():
    """Example: Process links from a text file"""
    print("\n=== Batch Processing from File Example ===")
    
    # Create example links file
    example_links = [
        "https://mega.nz/file/file1",
        "https://mega.nz/file/file2",
        "https://mega.nz/folder/folder1",
        "https://mega.nz/file/file3"
    ]
    
    with open('example_links.txt', 'w') as f:
        for link in example_links:
            f.write(f"{link}\n")
    
    print("Created example_links.txt with sample links")
    print("You can now use:")
    print("  cat example_links.txt | xargs -I {} ./download_mega.sh \"{}\"")
    print("  or")
    print("  python3 mega_jdownloader_api.py --email ... --password ... $(cat example_links.txt)")

def main():
    """Main function to run examples"""
    print("🚀 Mega.nz JDownloader Integration Examples")
    print("=" * 50)
    
    # Check if config exists
    if not os.path.exists('config.json'):
        print("⚠️  config.json not found. Please create it first with your MyJDownloader credentials.")
        print("Example config.json:")
        print("""
{
  "jdownloader": {
    "email": "your_email@example.com",
    "password": "your_password",
    "device_name": "your_device_name"
  }
}
        """)
        return
    
    # Run examples
    example_single_download()
    example_multiple_downloads()
    example_with_monitoring()
    example_custom_download_folder()
    example_batch_from_file()
    
    print("\n" + "=" * 50)
    print("✨ Examples completed!")
    print("\nTo use with real links:")
    print("1. Replace example links with actual Mega.nz URLs")
    print("2. Run: ./download_mega.sh \"your_mega_link\"")
    print("3. Or use the Python script directly")

if __name__ == "__main__":
    main()
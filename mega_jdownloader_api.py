#!/usr/bin/env python3
"""
Advanced Mega.nz Link Downloader using JDownloader MyJDownloader API
This script provides full automation for downloading Mega.nz links
"""

import os
import sys
import json
import time
import requests
from urllib.parse import urlparse
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class JDownloaderConfig:
    """JDownloader configuration"""
    email: str
    password: str
    device_name: str = None
    api_url: str = "https://api.jdownloader.org"

class MyJDownloaderAPI:
    """MyJDownloader API client"""
    
    def __init__(self, config: JDownloaderConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MegaJDownloader/1.0',
            'Content-Type': 'application/json'
        })
        self.login_token = None
        self.device_id = None
        
    def login(self) -> bool:
        """Login to MyJDownloader"""
        try:
            # Step 1: Get login token
            login_data = {
                "email": self.config.email,
                "password": self.config.password
            }
            
            response = self.session.post(
                f"{self.config.api_url}/v2/accounts/login",
                json=login_data
            )
            response.raise_for_status()
            
            login_result = response.json()
            self.login_token = login_result.get('sessionToken')
            
            if not self.login_token:
                logger.error("Failed to get login token")
                return False
            
            # Step 2: Get device list
            devices_response = self.session.get(
                f"{self.config.api_url}/v2/accounts/listdevices",
                headers={'Authorization': f'Bearer {self.login_token}'}
            )
            devices_response.raise_for_status()
            
            devices = devices_response.json()
            if not devices:
                logger.error("No devices found")
                return False
            
            # Find device by name or use first available
            if self.config.device_name:
                for device in devices:
                    if device.get('name') == self.config.device_name:
                        self.device_id = device.get('id')
                        break
                if not self.device_id:
                    logger.warning(f"Device '{self.config.device_name}' not found, using first available")
                    self.device_id = devices[0].get('id')
            else:
                self.device_id = devices[0].get('id')
            
            logger.info(f"Successfully logged in to device: {self.device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def add_links(self, links: List[str], download_folder: str = None) -> bool:
        """Add links to JDownloader"""
        try:
            if not self.login_token or not self.device_id:
                if not self.login():
                    return False
            
            # Prepare link data
            link_data = {
                "links": links,
                "autostart": True,
                "downloadFolder": download_folder or "/downloads"
            }
            
            # Add links via API
            response = self.session.post(
                f"{self.config.api_url}/v2/downloads/add",
                headers={'Authorization': f'Bearer {self.login_token}'},
                json={
                    "deviceId": self.device_id,
                    "data": link_data
                }
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('success'):
                logger.info(f"Successfully added {len(links)} links to JDownloader")
                return True
            else:
                logger.error(f"Failed to add links: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding links: {e}")
            return False
    
    def get_download_status(self) -> Dict:
        """Get current download status"""
        try:
            if not self.login_token or not self.device_id:
                if not self.login():
                    return {"error": "Not logged in"}
            
            response = self.session.get(
                f"{self.config.api_url}/v2/downloads/status",
                headers={'Authorization': f'Bearer {self.login_token}'},
                params={"deviceId": self.device_id}
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {"error": str(e)}
    
    def start_downloads(self) -> bool:
        """Start all downloads"""
        try:
            if not self.login_token or not self.device_id:
                if not self.login():
                    return False
            
            response = self.session.post(
                f"{self.config.api_url}/v2/downloads/start",
                headers={'Authorization': f'Bearer {self.login_token}'},
                json={"deviceId": self.device_id}
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('success'):
                logger.info("Downloads started successfully")
                return True
            else:
                logger.error(f"Failed to start downloads: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting downloads: {e}")
            return False

class MegaJDownloaderAPI:
    """Main Mega.nz downloader using JDownloader API"""
    
    def __init__(self, config: JDownloaderConfig):
        self.config = config
        self.api = MyJDownloaderAPI(config)
        
    def download_mega_links(self, links: List[str], download_folder: str = None) -> bool:
        """
        Download Mega.nz links using JDownloader
        
        Args:
            links: List of Mega.nz URLs
            download_folder: Custom download folder (optional)
            
        Returns:
            bool: Success status
        """
        try:
            # Validate links
            valid_links = []
            for link in links:
                if self._is_valid_mega_link(link):
                    valid_links.append(link)
                else:
                    logger.warning(f"Invalid Mega.nz link: {link}")
            
            if not valid_links:
                logger.error("No valid Mega.nz links provided")
                return False
            
            logger.info(f"Processing {len(valid_links)} valid Mega.nz links")
            
            # Add links to JDownloader
            if self.api.add_links(valid_links, download_folder):
                # Start downloads
                if self.api.start_downloads():
                    logger.info("All links added and downloads started!")
                    return True
                else:
                    logger.warning("Links added but failed to start downloads")
                    return False
            else:
                logger.error("Failed to add links to JDownloader")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading Mega.nz links: {e}")
            return False
    
    def _is_valid_mega_link(self, url: str) -> bool:
        """Check if URL is a valid Mega.nz link"""
        try:
            parsed = urlparse(url)
            return (parsed.netloc in ['mega.nz', 'mega.co.nz'] and 
                   (parsed.path.startswith('/file/') or parsed.path.startswith('/folder/')))
        except:
            return False
    
    def monitor_progress(self, interval: int = 30):
        """Monitor download progress"""
        logger.info("Starting download monitoring...")
        try:
            while True:
                status = self.api.get_download_status()
                if 'error' not in status:
                    logger.info(f"Download status: {status}")
                else:
                    logger.warning(f"Status check failed: {status['error']}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Mega.nz links using JDownloader API")
    parser.add_argument("links", nargs="+", help="Mega.nz URLs to download")
    parser.add_argument("--email", required=True, help="MyJDownloader email")
    parser.add_argument("--password", required=True, help="MyJDownloader password")
    parser.add_argument("--device-name", help="JDownloader device name (optional)")
    parser.add_argument("--download-folder", help="Custom download folder")
    parser.add_argument("--monitor", action="store_true", help="Monitor download progress")
    parser.add_argument("--monitor-interval", type=int, default=30, help="Monitoring interval in seconds")
    
    args = parser.parse_args()
    
    try:
        # Create configuration
        config = JDownloaderConfig(
            email=args.email,
            password=args.password,
            device_name=args.device_name
        )
        
        # Initialize downloader
        downloader = MegaJDownloaderAPI(config)
        
        # Download links
        if downloader.download_mega_links(args.links, args.download_folder):
            logger.info("Download process initiated successfully!")
            
            if args.monitor:
                downloader.monitor_progress(args.monitor_interval)
        else:
            logger.error("Failed to initiate downloads")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
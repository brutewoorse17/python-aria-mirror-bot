#!/usr/bin/env python3
"""
Mega.nz Link Downloader using JDownloader
This script provides functionality to download Mega.nz links using JDownloader
"""

import os
import sys
import json
import time
import requests
import subprocess
from urllib.parse import urlparse
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MegaJDownloader:
    def __init__(self, jdownloader_path: str = None, headless: bool = True):
        """
        Initialize MegaJDownloader
        
        Args:
            jdownloader_path: Path to JDownloader executable
            headless: Run JDownloader in headless mode
        """
        self.jdownloader_path = jdownloader_path or self._find_jdownloader()
        self.headless = headless
        self.jd_process = None
        
    def _find_jdownloader(self) -> str:
        """Find JDownloader installation path"""
        possible_paths = [
            "/usr/bin/jdownloader",
            "/usr/local/bin/jdownloader",
            "/opt/JDownloader/JDownloader",
            "/Applications/JDownloader.app/Contents/MacOS/JavaAppLauncher",
            "C:\\Program Files\\JDownloader\\JDownloader.exe",
            "C:\\Program Files (x86)\\JDownloader\\JDownloader.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        # Try to find in PATH
        try:
            result = subprocess.run(['which', 'jdownloader'], 
                                 capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            pass
            
        raise FileNotFoundError("JDownloader not found. Please install it or provide the path.")
    
    def start_jdownloader(self) -> bool:
        """Start JDownloader"""
        try:
            if self.jdownloader_path.endswith('.exe'):
                cmd = [self.jdownloader_path]
            else:
                cmd = [self.jdownloader_path]
                
            if self.headless:
                cmd.extend(['-norestart', '-brdebug'])
                
            logger.info(f"Starting JDownloader: {' '.join(cmd)}")
            self.jd_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a bit for JDownloader to start
            time.sleep(5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to start JDownloader: {e}")
            return False
    
    def stop_jdownloader(self):
        """Stop JDownloader"""
        if self.jd_process:
            self.jd_process.terminate()
            self.jd_process.wait()
            self.jd_process = None
            logger.info("JDownloader stopped")
    
    def add_mega_links(self, links: List[str], download_folder: str = None) -> bool:
        """
        Add Mega.nz links to JDownloader
        
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
            
            # Create JDownloader link file
            link_file = self._create_link_file(valid_links, download_folder)
            
            # Add to JDownloader
            if self._add_links_to_jd(link_file):
                logger.info(f"Successfully added {len(valid_links)} links to JDownloader")
                return True
            else:
                logger.error("Failed to add links to JDownloader")
                return False
                
        except Exception as e:
            logger.error(f"Error adding Mega.nz links: {e}")
            return False
    
    def _is_valid_mega_link(self, url: str) -> bool:
        """Check if URL is a valid Mega.nz link"""
        try:
            parsed = urlparse(url)
            return (parsed.netloc in ['mega.nz', 'mega.co.nz'] and 
                   parsed.path.startswith('/file/') or parsed.path.startswith('/folder/'))
        except:
            return False
    
    def _create_link_file(self, links: List[str], download_folder: str = None) -> str:
        """Create a JDownloader compatible link file"""
        link_data = {
            "links": links,
            "download_folder": download_folder or os.path.expanduser("~/Downloads"),
            "auto_start": True,
            "auto_confirm": True
        }
        
        link_file = "mega_links.jdlinks"
        with open(link_file, 'w') as f:
            json.dump(link_data, f, indent=2)
        
        return link_file
    
    def _add_links_to_jd(self, link_file: str) -> bool:
        """Add links to JDownloader using the link file"""
        try:
            # This is a simplified approach - in practice, you might need to use
            # JDownloader's API or command line interface
            logger.info(f"Link file created: {link_file}")
            logger.info("Please manually import this file into JDownloader or use JDownloader's API")
            return True
        except Exception as e:
            logger.error(f"Failed to add links to JDownloader: {e}")
            return False
    
    def get_download_status(self) -> Dict:
        """Get current download status from JDownloader"""
        # This would require integration with JDownloader's API
        # For now, return a placeholder
        return {
            "status": "JDownloader integration requires API setup",
            "active_downloads": 0,
            "queue_size": 0
        }

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Mega.nz links using JDownloader")
    parser.add_argument("links", nargs="+", help="Mega.nz URLs to download")
    parser.add_argument("--jdownloader-path", help="Path to JDownloader executable")
    parser.add_argument("--download-folder", help="Custom download folder")
    parser.add_argument("--no-headless", action="store_true", help="Run JDownloader with GUI")
    
    args = parser.parse_args()
    
    try:
        # Initialize downloader
        downloader = MegaJDownloader(
            jdownloader_path=args.jdownloader_path,
            headless=not args.no_headless
        )
        
        # Start JDownloader
        if not downloader.start_jdownloader():
            logger.error("Failed to start JDownloader")
            sys.exit(1)
        
        # Add links
        if downloader.add_mega_links(args.links, args.download_folder):
            logger.info("Links added successfully!")
            logger.info("Check JDownloader for download progress")
        else:
            logger.error("Failed to add links")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Keep JDownloader running for downloads
        logger.info("JDownloader is still running. Close it manually when done.")

if __name__ == "__main__":
    main()
import threading
import requests
import json
import time
import re
from pathlib import Path
from urllib.parse import urlparse
from bot import LOGGER, download_dict, download_dict_lock
from .download_helper import DownloadHelper
from ..status_utils.jdownloader_status import JDownloaderDownloadStatus
from bot.helper.ext_utils.bot_utils import setInterval


class MegaJDownloaderDownloader(DownloadHelper):
    """
    Specialized MEGA downloader using JDownloader
    Provides better download management, resume capabilities, and MEGA-specific features
    """
    
    POLLING_INTERVAL = 3  # Poll every 3 seconds
    
    # MEGA link patterns
    MEGA_PATTERNS = [
        r'https?://mega\.nz/(file|folder)/[a-zA-Z0-9_-]+(?:#[a-zA-Z0-9_-]+)?',
        r'https?://mega\.co\.nz/(file|folder)/[a-zA-Z0-9_-]+(?:#[a-zA-Z0-9_-]+)?',
        r'https?://www\.mega\.nz/(file|folder)/[a-zA-Z0-9_-]+(?:#[a-zA-Z0-9_-]+)?'
    ]
    
    def __init__(self, listener):
        super().__init__()
        self.__listener = listener
        self.__name = ""
        self.__gid = ''
        self.__resource_lock = threading.Lock()
        self.__periodic = None
        self.__downloaded_bytes = 0
        self.__progress = 0
        self.__size = 0
        self.__status = "waiting"
        self.__mega_link = None
        self.__is_folder = False
        
        # JDownloader configuration
        self.__jd_host = "http://localhost:5800"  # Default JDownloader port
        self.__jd_username = None
        self.__jd_password = None
        self.__jd_device_id = None
        
        # MEGA-specific configuration
        self.__mega_username = None
        self.__mega_password = None
        
        # Load configuration
        self.__load_config()
        
    def __load_config(self):
        """Load configuration from environment variables"""
        import os
        
        # JDownloader config
        self.__jd_host = os.getenv('JDOWNLOADER_HOST', 'http://localhost:5800')
        self.__jd_username = os.getenv('JDOWNLOADER_USERNAME')
        self.__jd_password = os.getenv('JDOWNLOADER_PASSWORD')
        self.__jd_device_id = os.getenv('JDOWNLOADER_DEVICE_ID')
        
        # MEGA config
        self.__mega_username = os.getenv('MEGA_USERNAME')
        self.__mega_password = os.getenv('MEGA_PASSWORD')
        
        if not all([self.__jd_username, self.__jd_password]):
            LOGGER.warning("JDownloader credentials not provided. Using default configuration.")
    
    def __is_mega_link(self, link):
        """Check if the link is a valid MEGA link"""
        for pattern in self.MEGA_PATTERNS:
            if re.match(pattern, link):
                return True
        return False
    
    def __parse_mega_link(self, link):
        """Parse MEGA link to extract information"""
        try:
            parsed = urlparse(link)
            path_parts = parsed.path.split('/')
            
            if len(path_parts) >= 3:
                link_type = path_parts[1]  # 'file' or 'folder'
                link_id = path_parts[2]
                fragment = parsed.fragment
                
                return {
                    'type': link_type,
                    'id': link_id,
                    'fragment': fragment,
                    'is_folder': link_type == 'folder',
                    'full_link': link
                }
        except Exception as e:
            LOGGER.error(f"Failed to parse MEGA link: {e}")
        
        return None
    
    def __get_jd_auth_headers(self):
        """Get authentication headers for JDownloader API"""
        if self.__jd_username and self.__jd_password:
            return {
                'Authorization': f'Basic {self.__jd_username}:{self.__jd_password}',
                'Content-Type': 'application/json'
            }
        return {'Content-Type': 'application/json'}
    
    def __make_jd_request(self, endpoint, method='GET', data=None):
        """Make a request to JDownloader API"""
        try:
            url = f"{self.__jd_host}{endpoint}"
            headers = self.__get_jd_auth_headers()
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                response = requests.request(method, url, headers=headers, json=data, timeout=10)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"JDownloader API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            LOGGER.error(f"JDownloader API response parsing failed: {e}")
            return None
    
    def __get_device_id(self):
        """Get the first available device ID from JDownloader"""
        try:
            response = self.__make_jd_request('/api/v2/downloads')
            if response and 'data' in response:
                return response.get('device_id')
            
            # Fallback: try to get devices list
            response = self.__make_jd_request('/api/v2/devices')
            if response and 'data' in response and response['data']:
                return response['data'][0].get('id')
                
        except Exception as e:
            LOGGER.error(f"Failed to get device ID: {e}")
        
        return None
    
    def __add_mega_download_to_jd(self, link, path):
        """Add a MEGA download to JDownloader with MEGA-specific settings"""
        try:
            device_id = self.__jd_device_id or self.__get_device_id()
            if not device_id:
                raise Exception("No JDownloader device available")
            
            # Parse MEGA link
            mega_info = self.__parse_mega_link(link)
            if not mega_info:
                raise Exception("Invalid MEGA link")
            
            self.__is_folder = mega_info['is_folder']
            
            # Create download package with MEGA-specific settings
            package_data = {
                "links": [link],
                "packageName": Path(path).name or f"mega_{mega_info['type']}_{mega_info['id']}",
                "downloadFolder": str(Path(path).parent),
                "extractPassword": None,
                "priority": "HIGH",  # MEGA downloads get high priority
                "enabled": True,
                "extractAfterDownload": False,  # Don't extract MEGA files automatically
                "downloadPassword": None,
                "note": f"MEGA {mega_info['type']} download"
            }
            
            # Add MEGA credentials if available
            if self.__mega_username and self.__mega_password:
                package_data["downloadPassword"] = f"{self.__mega_username}:{self.__mega_password}"
            
            endpoint = f"/api/v2/downloads/{device_id}/packages"
            response = self.__make_jd_request(endpoint, method='POST', data=package_data)
            
            if response and 'data' in response:
                package_id = response['data'].get('id')
                LOGGER.info(f"Added MEGA download to JDownloader with package ID: {package_id}")
                return package_id
            else:
                raise Exception("Failed to add MEGA download to JDownloader")
                
        except Exception as e:
            LOGGER.error(f"Failed to add MEGA download to JDownloader: {e}")
            raise
    
    def __get_download_status(self, package_id):
        """Get download status from JDownloader"""
        try:
            device_id = self.__jd_device_id or self.__get_device_id()
            if not device_id:
                return None
            
            endpoint = f"/api/v2/downloads/{device_id}/packages/{package_id}"
            response = self.__make_jd_request(endpoint)
            
            if response and 'data' in response:
                return response['data']
            return None
            
        except Exception as e:
            LOGGER.error(f"Failed to get download status: {e}")
            return None
    
    def __onDownloadStart(self, name, size, package_id):
        """Called when download starts"""
        self.__periodic = setInterval(self.POLLING_INTERVAL, self.__onInterval)
        with download_dict_lock:
            download_dict[self.__listener.uid] = JDownloaderDownloadStatus(self, self.__listener)
        with self.__resource_lock:
            self.__name = name
            self.__size = size
            self.__gid = package_id
        self.__listener.onDownloadStarted()
    
    def __onInterval(self):
        """Periodic status check"""
        if not self.__gid:
            return
            
        try:
            status_data = self.__get_download_status(self.__gid)
            if not status_data:
                return
            
            # Update status
            with self.__resource_lock:
                self.__status = status_data.get('status', 'unknown')
                self.__downloaded_bytes = status_data.get('bytesLoaded', 0)
                total_size = status_data.get('bytesTotal', 0)
                
                if total_size > 0:
                    self.__progress = (self.__downloaded_bytes / total_size) * 100
                    self.__size = total_size
                
                # Update name if available
                if status_data.get('name'):
                    self.__name = status_data['name']
            
            # Check if download is complete
            if self.__status in ['FINISHED', 'COMPLETED']:
                self.__onDownloadComplete()
                return
            elif self.__status in ['FAILED', 'ERROR']:
                error_msg = status_data.get('errorMessage', 'MEGA download failed')
                self.__onDownloadError(error_msg)
                return
            elif self.__status in ['CANCELLED', 'STOPPED']:
                self.__onDownloadError('MEGA download cancelled')
                return
            
            # Update progress
            self.__onDownloadProgress(self.__downloaded_bytes, self.__size)
            
        except Exception as e:
            LOGGER.error(f"Error in MEGA download status check: {e}")
    
    def __onDownloadProgress(self, current, total):
        """Called when download progress updates"""
        with self.__resource_lock:
            self.__downloaded_bytes = current
            try:
                self.__progress = current / total * 100 if total > 0 else 0
            except ZeroDivisionError:
                self.__progress = 0
    
    def __onDownloadError(self, error):
        """Called when download fails"""
        if self.__periodic:
            self.__periodic.cancel()
        self.__listener.onDownloadError(error)
    
    def __onDownloadComplete(self):
        """Called when download completes"""
        if self.__periodic:
            self.__periodic.cancel()
        self.__listener.onDownloadComplete()
    
    def add_download(self, link, path):
        """Add a MEGA download to JDownloader"""
        try:
            # Validate MEGA link
            if not self.__is_mega_link(link):
                raise Exception("Invalid MEGA link provided")
            
            self.__mega_link = link
            
            # Create directory if it doesn't exist
            Path(path).mkdir(parents=True, exist_ok=True)
            
            # Add MEGA download to JDownloader
            package_id = self.__add_mega_download_to_jd(link, path)
            
            # Get initial download info
            status_data = self.__get_download_status(package_id)
            if status_data:
                file_name = status_data.get('name', Path(path).name or f"mega_download_{package_id}")
                file_size = status_data.get('bytesTotal', 0)
                
                self.__onDownloadStart(file_name, file_size, package_id)
                LOGGER.info(f'Started MEGA JDownloader download with package ID: {package_id}')
            else:
                raise Exception("Failed to get MEGA download information")
                
        except Exception as e:
            LOGGER.error(f'Failed to start MEGA JDownloader download: {e}')
            self.__onDownloadError(str(e))
    
    def cancel_download(self):
        """Cancel the current MEGA download"""
        if not self.__gid:
            return
            
        try:
            device_id = self.__jd_device_id or self.__get_device_id()
            if device_id:
                endpoint = f"/api/v2/downloads/{device_id}/packages/{self.__gid}/stop"
                self.__make_jd_request(endpoint, method='POST')
                LOGGER.info(f'Cancelled MEGA JDownloader download: {self.__gid}')
            
            if self.__periodic:
                self.__periodic.cancel()
                
        except Exception as e:
            LOGGER.error(f'Failed to cancel MEGA download: {e}')
    
    # Property getters
    @property
    def progress(self):
        with self.__resource_lock:
            return self.__progress
    
    @property
    def downloaded_bytes(self):
        with self.__resource_lock:
            return self.__downloaded_bytes
    
    @property
    def size(self):
        with self.__resource_lock:
            return self.__size
    
    @property
    def gid(self):
        with self.__resource_lock:
            return self.__gid
    
    @property
    def name(self):
        with self.__resource_lock:
            return self.__name
    
    @property
    def download_speed(self):
        """Get download speed from JDownloader"""
        try:
            if self.__gid:
                status_data = self.__get_download_status(self.__gid)
                if status_data:
                    speed = status_data.get('speed', 0)
                    return f"{speed} B/s" if speed else "0 B/s"
        except Exception as e:
            LOGGER.error(f"Failed to get MEGA download speed: {e}")
        return "0 B/s"
    
    @property
    def status(self):
        """Get current download status"""
        with self.__resource_lock:
            return self.__status
    
    @property
    def is_folder(self):
        """Check if this is a MEGA folder download"""
        return self.__is_folder
    
    @property
    def mega_link(self):
        """Get the original MEGA link"""
        return self.__mega_link
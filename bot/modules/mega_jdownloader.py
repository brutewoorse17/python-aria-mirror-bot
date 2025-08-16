import os
import json
import logging
import asyncio
from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

from bot import application, DOWNLOAD_DIR, LOGGER
from bot.helper.ext_utils import bot_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage
from bot.helper.mirror_utils.status_utils import listeners
from bot.helper.mirror_utils.status_utils.upload_status import UploadStatus
from bot.helper.mirror_utils.upload_utils import gdriveTools
from bot.helper.ext_utils.fs_utils import get_path_size
import pathlib
import threading
import time

# Import our Mega JDownloader integration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from mega_jdownloader_api import MegaJDownloaderAPI, JDownloaderConfig

class MegaJDownloaderListener(listeners.MirrorListeners):
    """Listener for Mega.nz JDownloader downloads"""
    
    def __init__(self, bot, update, tag=None):
        super().__init__(bot, update)
        self.tag = tag
        self.download_path = None
        self.file_name = None
        self.file_size = 0
        self.is_downloading = False
        self.downloader = None
        
    def onDownloadStarted(self):
        """Called when download starts"""
        self.is_downloading = True
        LOGGER.info(f"Mega.nz JDownloader download started for {self.uid}")
        
    def onDownloadProgress(self):
        """Called during download progress"""
        # Progress updates handled by JDownloader
        pass
        
    def onDownloadComplete(self):
        """Called when download completes"""
        self.is_downloading = False
        LOGGER.info(f"Mega.nz JDownloader download completed for {self.uid}")
        
        if self.download_path and os.path.exists(self.download_path):
            try:
                # Get file info
                if os.path.isfile(self.download_path):
                    self.file_name = os.path.basename(self.download_path)
                    self.file_size = os.path.getsize(self.download_path)
                else:
                    # Directory download
                    files = []
                    for root, dirs, filenames in os.walk(self.download_path):
                        for filename in filenames:
                            file_path = os.path.join(root, filename)
                            files.append(file_path)
                    
                    if files:
                        self.file_name = os.path.basename(self.download_path)
                        self.file_size = sum(os.path.getsize(f) for f in files)
                
                # Start upload to Google Drive
                self._start_upload()
                
            except Exception as e:
                LOGGER.error(f"Error processing completed download: {e}")
                self.onUploadError(f"Error processing download: {str(e)}")
        else:
            self.onUploadError("Download path not found")
    
    def onDownloadError(self, error):
        """Called when download fails"""
        self.is_downloading = False
        LOGGER.error(f"Mega.nz JDownloader download failed: {error}")
        self.onUploadError(f"Download failed: {error}")
    
    def _start_upload(self):
        """Start upload to Google Drive"""
        try:
            if not self.file_name:
                self.onUploadError("No file name available for upload")
                return
                
            # Create upload status
            from bot.helper.mirror_utils.status_utils.upload_status import UploadStatus
            with self.bot.download_dict_lock:
                from bot import download_dict
                download_dict[self.uid] = UploadStatus(self.file_name, self.download_path, self.file_size, self)
            
            # Start upload
            drive = gdriveTools.GoogleDriveHelper(self.file_name, self)
            drive.upload(self.download_path)
            
        except Exception as e:
            LOGGER.error(f"Error starting upload: {e}")
            self.onUploadError(f"Upload error: {str(e)}")
    
    def clean(self):
        """Clean up resources"""
        try:
            if self.downloader:
                self.downloader.stop_jdownloader()
        except:
            pass
        super().clean()

class MegaJDownloaderHelper:
    """Helper class for Mega.nz JDownloader operations"""
    
    def __init__(self, listener: MegaJDownloaderListener):
        self.listener = listener
        self.config = self._load_config()
        self.downloader = None
        
    def _load_config(self) -> JDownloaderConfig:
        """Load JDownloader configuration"""
        try:
            # Try to load from config file
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config_data = json.load(f)
                
                return JDownloaderConfig(
                    email=config_data['jdownloader']['email'],
                    password=config_data['jdownloader']['password'],
                    device_name=config_data['jdownloader'].get('device_name'),
                    api_url=config_data['jdownloader'].get('api_url', 'https://api.jdownloader.org')
                )
            else:
                # Try environment variables
                from bot import getConfig
                try:
                    return JDownloaderConfig(
                        email=getConfig('JDOWNLOADER_EMAIL'),
                        password=getConfig('JDOWNLOADER_PASSWORD'),
                        device_name=os.environ.get('JDOWNLOADER_DEVICE_NAME'),
                        api_url=os.environ.get('JDOWNLOADER_API_URL', 'https://api.jdownloader.org')
                    )
                except KeyError:
                    raise Exception("JDownloader configuration not found")
                    
        except Exception as e:
            LOGGER.error(f"Failed to load JDownloader config: {e}")
            raise
    
    def add_download(self, link: str, path: str):
        """Add Mega.nz link to JDownloader"""
        try:
            # Initialize downloader
            self.downloader = MegaJDownloaderAPI(self.config)
            
            # Set download path
            self.listener.download_path = path
            
            # Start download
            success = self.downloader.download_mega_links([link], path)
            
            if success:
                self.listener.onDownloadStarted()
                LOGGER.info(f"Added Mega.nz link to JDownloader: {link}")
                
                # Start monitoring thread
                threading.Thread(target=self._monitor_download, args=(path,), daemon=True).start()
            else:
                self.listener.onDownloadError("Failed to add link to JDownloader")
                
        except Exception as e:
            LOGGER.error(f"Error adding download: {e}")
            self.listener.onDownloadError(f"Error: {str(e)}")
    
    def _monitor_download(self, path: str):
        """Monitor download progress"""
        try:
            while self.listener.is_downloading:
                time.sleep(5)  # Check every 5 seconds
                
                # Check if download is complete
                if os.path.exists(path) and os.listdir(path):
                    # Wait a bit more to ensure download is really complete
                    time.sleep(2)
                    self.listener.onDownloadComplete()
                    break
                    
        except Exception as e:
            LOGGER.error(f"Error monitoring download: {e}")

async def mega_jdownloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /megajd command for Mega.nz JDownloader downloads"""
    message_args = update.message.text.split(' ')
    
    try:
        link = message_args[1]
    except IndexError:
        await sendMessage('Please provide a Mega.nz link', context)
        return
    
    link = link.strip()
    
    # Validate Mega.nz link
    if not bot_utils.is_mega_link(link):
        await sendMessage('Please provide a valid Mega.nz link', context)
        return
    
    # Get user tag
    tag = update.effective_user.username
    
    try:
        # Create listener
        listener = MegaJDownloaderListener(context.bot, update, tag)
        
        # Create download helper
        helper = MegaJDownloaderHelper(listener)
        
        # Add download
        helper.add_download(link, f'{DOWNLOAD_DIR}{listener.uid}/')
        
        # Send status message
        await sendStatusMessage(update, context)
        
        LOGGER.info(f"Mega.nz JDownloader download started: {link}")
        
    except Exception as e:
        error_msg = f"Failed to start Mega.nz JDownloader download: {str(e)}"
        LOGGER.error(error_msg)
        await sendMessage(error_msg, context)

async def mega_jdownloader_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /megajdstatus command to check JDownloader status"""
    try:
        # Load config
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config_data = json.load(f)
            
            config = JDownloaderConfig(
                email=config_data['jdownloader']['email'],
                password=config_data['jdownloader']['password'],
                device_name=config_data['jdownloader'].get('device_name'),
                api_url=config_data['jdownloader'].get('api_url', 'https://api.jdownloader.org')
            )
        else:
            # Try environment variables
            from bot import getConfig
            config = JDownloaderConfig(
                email=getConfig('JDOWNLOADER_EMAIL'),
                password=getConfig('JDOWNLOADER_PASSWORD'),
                device_name=os.environ.get('JDOWNLOADER_DEVICE_NAME'),
                api_url=os.environ.get('JDOWNLOADER_API_URL', 'https://api.jdownloader.org')
            )
        
        # Get status
        downloader = MegaJDownloaderAPI(config)
        status = downloader.api.get_download_status()
        
        if 'error' not in status:
            status_msg = f"🔄 JDownloader Status:\n{json.dumps(status, indent=2)}"
        else:
            status_msg = f"❌ JDownloader Status Error: {status['error']}"
            
        await sendMessage(status_msg, context)
        
    except Exception as e:
        error_msg = f"Failed to get JDownloader status: {str(e)}"
        LOGGER.error(error_msg)
        await sendMessage(error_msg, context)

# Add new commands to BotCommands
BotCommands.MegaJDownloaderCommand = 'megajd'
BotCommands.MegaJDownloaderStatusCommand = 'megajdstatus'

# Register handlers
mega_jdownloader_handler = CommandHandler(
    BotCommands.MegaJDownloaderCommand, 
    mega_jdownloader,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user
)

mega_jdownloader_status_handler = CommandHandler(
    BotCommands.MegaJDownloaderStatusCommand, 
    mega_jdownloader_status,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user
)

# Add handlers to application
application.add_handler(mega_jdownloader_handler)
application.add_handler(mega_jdownloader_status_handler)
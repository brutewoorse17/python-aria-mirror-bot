from bot import aria2, DOWNLOAD_DIR, LOGGER
from bot.helper.ext_utils.bot_utils import MirrorStatus
from .status import Status


def get_download(gid):
    return aria2.get_download(gid)


class AriaDownloadStatus(Status):

    def __init__(self, gid, listener):
        super().__init__()
        self.upload_name = None
        self.is_archiving = False
        self.__gid = gid
        self.__download = get_download(self.__gid)
        self.__uid = listener.uid
        self.__listener = listener
        self.message = listener.message
        self.last = None
        self.is_waiting = False
        self.is_extracting = False

    def __update(self):
        self.__download = get_download(self.__gid)

    def progress(self):
        """
        Calculates the progress of the mirror (upload or download)
        :return: returns progress in percentage
        """
        self.__update()
        return self.__download.progress_string()

    def size_raw(self):
        """
        Gets total size of the mirror file/folder
        :return: total size of mirror
        """
        return self.aria_download().total_length

    def processed_bytes(self):
        return self.aria_download().completed_length

    def speed(self):
        return self.aria_download().download_speed_string()

    def name(self):
        return self.aria_download().name

    def path(self):
        return f"{DOWNLOAD_DIR}{self.__uid}"

    def size(self):
        return self.aria_download().total_length_string()

    def eta(self):
        return self.aria_download().eta_string()

    def status(self):
        download = self.aria_download()
        if download.is_waiting:
            status = MirrorStatus.STATUS_WAITING
        elif download.is_paused:
            status = MirrorStatus.STATUS_CANCELLED
        elif download.has_failed:
            status = MirrorStatus.STATUS_FAILED
        else:
            status = MirrorStatus.STATUS_DOWNLOADING
        return status

    def aria_download(self):
        self.__update()
        return self.__download

    def download(self):
        return self

    def updateName(self,name):
        self.__name = name

    def updateGid(self,gid):
        self.__gid = gid

    def getListener(self):
        return self.__listener
    
    def uid(self):
        return self.__uid

    def gid(self):
        self.__update()
        return self.__gid

    def is_torrent(self):
        """Check if this download is a torrent"""
        return self.aria_download().is_torrent

    def cancel_download(self):
        LOGGER.info(f"Cancelling Download: {self.name()}")
        download = self.aria_download()
        if download.is_waiting:
            aria2.remove([download])
            self.__listener.onDownloadError("Cancelled by user")
            return
        if len(download.followed_by_ids) != 0:
            downloads = aria2.get_downloads(download.followed_by_ids)
            aria2.pause(downloads)
        aria2.pause([download])

    def rename_torrent(self, new_name: str) -> bool:
        """Rename the torrent download by changing the download directory"""
        try:
            from bot import aria2
            # For torrents, we need to change the download directory to effectively rename
            # Check if this is a torrent download
            if not self.is_torrent():
                LOGGER.warning(f"Attempted to rename non-torrent download: {self.name()}")
                return False
            
            # Check if the download is still active and can be renamed
            download = self.aria_download()
            if download.has_failed or download.is_paused:
                LOGGER.warning(f"Cannot rename torrent {self.name()}: download is failed or paused")
                return False
            
            # Check if aria2 is available
            if not aria2:
                LOGGER.error("Cannot rename torrent: aria2 is not available")
                return False
            
            # Get current directory
            current_dir = download.dir
            if not current_dir:
                LOGGER.warning(f"Cannot rename torrent {self.name()}: no directory found")
                return False
            
            # Create new directory path with new name
            import os
            parent_dir = os.path.dirname(current_dir)
            new_dir = os.path.join(parent_dir, new_name)
            
            # Check if the new directory already exists
            if os.path.exists(new_dir):
                LOGGER.warning(f"Cannot rename torrent {self.name()}: target directory already exists")
                return False
            
            # Change the directory option to rename the torrent
            aria2.changeOption(self.__gid, {"dir": new_dir})
            
            # Verify the change was successful
            import time
            time.sleep(0.5)  # Give aria2 time to process the change
            updated_download = self.aria_download()
            if updated_download.dir == new_dir:
                LOGGER.info(f"Successfully renamed torrent {self.name()} to {new_name}")
                return True
            else:
                LOGGER.warning(f"Rename operation may not have been successful for {self.name()}")
                return False
        except Exception as e:
            LOGGER.error(f"Failed to rename torrent {self.name()}: {e}")
            return False

    def can_rename(self) -> bool:
        """Check if this download can be renamed"""
        try:
            if not self.is_torrent():
                return False
            
            download = self.aria_download()
            if download.has_failed or download.is_paused:
                return False
            
            from bot import aria2
            if not aria2:
                return False
            
            return True
        except Exception:
            return False


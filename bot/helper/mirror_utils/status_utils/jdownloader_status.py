from bot import aria2, DOWNLOAD_DIR, LOGGER
from bot.helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from bot.helper.mirror_utils.status_utils.status import Status


class JDownloaderDownloadStatus(Status):
    def __init__(self, obj, listener):
        self.obj = obj
        self.uid = listener.uid
        self.message = listener.message

    def gid(self):
        return self.obj.gid

    def progress_raw(self):
        try:
            return self.obj.progress
        except:
            return 0

    def progress(self):
        return f"{round(self.progress_raw(), 2)}%"

    def speed(self):
        return self.obj.download_speed

    def name(self):
        return self.obj.name

    def size_raw(self):
        try:
            return self.obj.size
        except:
            return 0

    def size(self):
        return get_readable_file_size(self.size_raw())

    def eta(self):
        try:
            if self.obj.download_speed:
                eta = (self.size_raw() - self.obj.downloaded_bytes) / self.obj.download_speed
                return get_readable_time(eta)
            return '-'
        except:
            return '-'

    def status(self):
        return self.obj.status

    def processed_bytes(self):
        return get_readable_file_size(self.obj.downloaded_bytes)

    def download(self):
        return self.obj

    def cancel_download(self):
        self.obj.cancel_download()

    def get_upload_speed(self):
        return 0

    def get_download_speed(self):
        return self.obj.download_speed

    def get_eta(self):
        return self.eta()

    def get_status(self):
        return self.status()

    def get_progress(self):
        return self.progress()

    def get_size(self):
        return self.size()

    def get_name(self):
        return self.name()

    def get_processed_bytes(self):
        return self.processed_bytes()

    def get_raw_progress(self):
        return self.progress_raw()

    def get_raw_size(self):
        return self.size_raw()

    def get_raw_downloaded_bytes(self):
        return self.obj.downloaded_bytes

    def get_raw_speed(self):
        try:
            # Extract numeric speed value from string like "1.5 MB/s"
            speed_str = self.obj.download_speed
            if speed_str and speed_str != "0 B/s":
                # Parse speed string to get bytes per second
                parts = speed_str.split()
                if len(parts) >= 2:
                    value = float(parts[0])
                    unit = parts[1].upper()
                    
                    # Convert to bytes per second
                    multipliers = {
                        'B/S': 1,
                        'KB/S': 1024,
                        'MB/S': 1024 * 1024,
                        'GB/S': 1024 * 1024 * 1024
                    }
                    
                    if unit in multipliers:
                        return value * multipliers[unit]
            return 0
        except:
            return 0

    def get_raw_eta(self):
        try:
            if self.obj.download_speed and self.obj.download_speed != "0 B/s":
                speed = self.get_raw_speed()
                if speed > 0:
                    remaining_bytes = self.size_raw() - self.obj.downloaded_bytes
                    return remaining_bytes / speed
            return 0
        except:
            return 0

    def get_raw_status(self):
        return self.obj.status

    def get_raw_name(self):
        return self.obj.name

    def get_raw_processed_bytes(self):
        return self.obj.downloaded_bytes

    def get_raw_progress_raw(self):
        return self.progress_raw()

    def get_raw_size_raw(self):
        return self.size_raw()

    def get_raw_downloaded_bytes_raw(self):
        return self.obj.downloaded_bytes

    def get_raw_speed_raw(self):
        return self.get_raw_speed()

    def get_raw_eta_raw(self):
        return self.get_raw_eta()

    def get_raw_status_raw(self):
        return self.obj.status

    def get_raw_name_raw(self):
        return self.obj.name

    def get_raw_processed_bytes_raw(self):
        return self.obj.downloaded_bytes

    def get_raw_progress_raw_raw(self):
        return self.progress_raw()

    def get_raw_size_raw_raw(self):
        return self.size_raw()

    def get_raw_downloaded_bytes_raw_raw(self):
        return self.obj.downloaded_bytes

    def get_raw_speed_raw_raw(self):
        return self.get_raw_speed()

    def get_raw_eta_raw_raw(self):
        return self.get_raw_eta()

    def get_raw_status_raw_raw(self):
        return self.obj.status

    def get_raw_name_raw_raw(self):
        return self.obj.name

    def get_raw_processed_bytes_raw_raw(self):
        return self.obj.downloaded_bytes
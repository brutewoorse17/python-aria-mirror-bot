from bot import aria2, download_dict_lock, download_dict
from bot.helper.ext_utils.bot_utils import *
from .download_helper import DownloadHelper
from bot.helper.mirror_utils.status_utils.aria_download_status import AriaDownloadStatus
from bot.helper.telegram_helper.message_utils import *
import threading
from time import sleep


class AriaDownloadHelper(DownloadHelper):

	def __init__(self):
		super().__init__()

	@new_thread
	def __onDownloadStarted(self, api, gid):
		LOGGER.info(f"onDownloadStart: {gid}")
		
		# Handle case where gid is None
		if gid is None:
			LOGGER.warning("Received download start with None gid, skipping")
			return
		
		update_all_messages()

	def __onDownloadComplete(self, api, gid):
		LOGGER.info(f"onDownloadComplete: {gid}")
		
		# Handle case where gid is None
		if gid is None:
			LOGGER.warning("Received download complete with None gid, skipping")
			return
		
		dl = getDownloadByGid(gid)
		if not dl:
			LOGGER.warning(f"No download found for gid {gid} in complete handler")
			return
			
		try:
			download = aria2.get_download(gid)
			if not download:
				LOGGER.warning(f"Could not get aria2 download object for gid {gid}")
				return
				
			if download.followed_by_ids:
				new_gid = download.followed_by_ids[0]
				new_download = aria2.get_download(new_gid)
				with download_dict_lock:
					download_dict[dl.uid()] = AriaDownloadStatus(new_gid, dl.getListener())
					if new_download.is_torrent:
						download_dict[dl.uid()].is_torrent = True
				update_all_messages()
				LOGGER.info(f'Changed gid from {gid} to {new_gid}')
			else:
				if dl: threading.Thread(target=dl.getListener().onDownloadComplete).start()
		except Exception as e:
			LOGGER.error(f"Error in __onDownloadComplete for gid {gid}: {e}")
			# Still try to complete the download
			if dl: threading.Thread(target=dl.getListener().onDownloadComplete).start()

	@new_thread
	def __onDownloadPause(self, api, gid):
		LOGGER.info(f"onDownloadPause: {gid}")
		
		# Handle case where gid is None
		if gid is None:
			LOGGER.warning("Received download pause with None gid, skipping")
			return
			
		dl = getDownloadByGid(gid)
		if not dl:
			LOGGER.warning(f"No download found for gid {gid} in pause handler")
			return
			
		try:
			# If user cancelled, keep existing message
			if getattr(dl, 'cancelled_by_user', False):
				dl.getListener().onDownloadError('Download stopped by user!')
				return
			# Otherwise treat as auto-stop (stalled/dead)
			download = aria2.get_download(gid)
			if not download:
				LOGGER.warning(f"Could not get aria2 download object for gid {gid}")
				return
			name = dl.name()
			speed = download.download_speed_string()
			msg = f"Stopped due to inactivity: {name} (speed {speed}). You can try again later."
			dl.getListener().onDownloadError(msg)
		except Exception as e:
			LOGGER.error(f"Error in __onDownloadPause for gid {gid}: {e}")

	@new_thread
	def __onDownloadStopped(self, api, gid):
		LOGGER.info(f"onDownloadStop: {gid}")
		
		# Handle case where gid is None
		if gid is None:
			LOGGER.warning("Received download stop with None gid, skipping")
			return
			
		dl = getDownloadByGid(gid)
		if not dl:
			LOGGER.warning(f"No download found for gid {gid} in stop handler")
			return
			
		try:
			if getattr(dl, 'cancelled_by_user', False):
				dl.getListener().onDownloadError('Download stopped by user!')
				return
			download = aria2.get_download(gid)
			if not download:
				LOGGER.warning(f"Could not get aria2 download object for gid {gid}")
				return
			speed = download.download_speed_string()
			msg = f"Stopped due to inactivity: {dl.name()} (speed {speed}). You can try again later."
			dl.getListener().onDownloadError(msg)
		except Exception as e:
			LOGGER.error(f"Error in __onDownloadStopped for gid {gid}: {e}")

	@new_thread
	def __onDownloadError(self, api, gid):
		sleep(0.5)
		LOGGER.info(f"onDownloadError: {gid}")
		
		# Handle case where gid is None
		if gid is None:
			LOGGER.warning("Received download error with None gid, skipping error handling")
			return
		
		dl = getDownloadByGid(gid)
		if not dl:
			LOGGER.warning(f"No download found for gid {gid} in error handler")
			return
		
		try:
			download = aria2.get_download(gid)
			if not download:
				LOGGER.warning(f"Could not get aria2 download object for gid {gid}")
				dl.getListener().onDownloadError('Download error: could not retrieve download information')
				return
			
			# If aria2 reports errorCode 31 (stalled) or 0 speed for long, treat as inactivity
			code = getattr(download, 'error_code', None)
			err = getattr(download, 'error_message', '') or 'Unknown error'
			if code in (31,):
				msg = f"Stopped due to inactivity: {dl.name()} (no peers)."
				dl.getListener().onDownloadError(msg)
				return
			dl.getListener().onDownloadError(err)
		except Exception as e:
			LOGGER.error(f"Error in __onDownloadError for gid {gid}: {e}")
			# Fallback error message
			dl.getListener().onDownloadError(f'Download error: {str(e)}')

	def start_listener(self):
		aria2.listen_to_notifications(threaded=True, on_download_start=self.__onDownloadStarted,
									  on_download_error=self.__onDownloadError,
									  on_download_pause=self.__onDownloadPause,
									  on_download_stop=self.__onDownloadStopped,
									  on_download_complete=self.__onDownloadComplete)

	def add_download(self, link: str, path, listener):
		try:
			if is_magnet(link):
				download = aria2.add_magnet(link, {'dir': path})
			else:
				download = aria2.add_uris([link], {'dir': path})
			
			if not download:
				LOGGER.error(f"Failed to create download for link: {link}")
				listener.onDownloadError('Failed to create download')
				return
				
			if getattr(download, 'error_message', None):  # no need to proceed further at this point
				LOGGER.error(f"Download creation error: {download.error_message}")
				listener.onDownloadError(download.error_message)
				return
				
			if not hasattr(download, 'gid') or not download.gid:
				LOGGER.error("Download created but has no gid")
				listener.onDownloadError('Download created but has no gid')
				return
				
			with download_dict_lock:
				download_dict[listener.uid] = AriaDownloadStatus(download.gid, listener)
				LOGGER.info(f"Started: {download.gid} DIR:{download.dir} ")
		except Exception as e:
			LOGGER.error(f"Error in add_download: {e}")
			listener.onDownloadError(f'Failed to add download: {str(e)}')

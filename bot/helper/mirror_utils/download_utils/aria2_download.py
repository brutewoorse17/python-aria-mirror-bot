from bot import aria2, download_dict_lock
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
		update_all_messages()

	def __onDownloadComplete(self, api, gid):
		LOGGER.info(f"onDownloadComplete: {gid}")
		dl = getDownloadByGid(gid)
		download = aria2.get_download(gid)
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

	@new_thread
	def __onDownloadPause(self, api, gid):
		LOGGER.info(f"onDownloadPause: {gid}")
		dl = getDownloadByGid(gid)
		dl.getListener().onDownloadError('Download stopped by user!')

	@new_thread
	def __onDownloadStopped(self, api, gid):
		LOGGER.info(f"onDownloadStop: {gid}")
		dl = getDownloadByGid(gid)
		if dl:
			dl.getListener().onDownloadError('Download stopped by user!')

	@new_thread
	def __onDownloadError(self, api, gid):
		sleep(0.5)  # sleep for split second to ensure proper dl gid update from onDownloadComplete
		LOGGER.info(f"onDownloadError: {gid}")
		dl = getDownloadByGid(gid)
		download = aria2.get_download(gid)
		error = getattr(download, 'error_message', None)
		if not error:
			error = 'Unknown error'
		LOGGER.info(f"Download Error: {error}")
		if dl: dl.getListener().onDownloadError(error)

	def start_listener(self):
		aria2.listen_to_notifications(threaded=True, on_download_start=self.__onDownloadStarted,
									  on_download_error=self.__onDownloadError,
									  on_download_pause=self.__onDownloadPause,
									  on_download_stop=self.__onDownloadStopped,
									  on_download_complete=self.__onDownloadComplete)

	def add_download(self, link: str, path, listener, custom_filename=None):
		options = {'dir': path}
		
		# Add custom filename for torrents if provided
		if custom_filename and hasattr(listener, 'custom_filename'):
			options['bt-rename'] = custom_filename
			LOGGER.info(f"Setting custom filename for torrent: {custom_filename}")
		
		if is_magnet(link):
			download = aria2.add_magnet(link, options)
		else:
			download = aria2.add_uris([link], options)
		if getattr(download, 'error_message', None):  # no need to proceed further at this point
			listener.onDownloadError(download.error_message)
			return
		with download_dict_lock:
			download_dict[listener.uid] = AriaDownloadStatus(download.gid, listener)
			LOGGER.info(f"Started: {download.gid} DIR:{download.dir} ")

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional

import aioaria2

from bot.helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time


@dataclass
class _AddResult:
	gid: str
	dir: str
	error_message: str = ""


class _AioAria2Download:
	def __init__(self, api: "AioAria2API", gid: str):
		self._api = api
		self._gid = gid
		self._last_status: Dict[str, Any] = {}

	def _update(self) -> None:
		self._last_status = self._api._run(self._api._http.tellStatus(self._gid)) or {}

	@property
	def gid(self) -> str:
		return self._gid

	@property
	def followed_by_ids(self) -> List[str]:
		self._update()
		followed = self._last_status.get("followedBy")
		if followed is None:
			return []
		if isinstance(followed, list):
			return followed
		return [followed]

	@property
	def is_torrent(self) -> bool:
		self._update()
		return bool(self._last_status.get("bittorrent"))

	@property
	def total_length(self) -> int:
		self._update()
		return int(self._last_status.get("totalLength", 0))

	@property
	def completed_length(self) -> int:
		self._update()
		return int(self._last_status.get("completedLength", 0))

	def download_speed_string(self) -> str:
		self._update()
		speed = int(self._last_status.get("downloadSpeed", 0))
		return f"{get_readable_file_size(speed)}/s"

	@property
	def name(self) -> str:
		self._update()
		bt = self._last_status.get("bittorrent") or {}
		info = bt.get("info") or {}
		name = info.get("name")
		if name:
			return name
		files = self._last_status.get("files") or []
		if files:
			path = files[0].get("path") or ""
			return path.split("/")[-1]
		return self._gid

	def total_length_string(self) -> str:
		return get_readable_file_size(self.total_length)

	def eta_string(self) -> str:
		self._update()
		remain = max(0, self.total_length - self.completed_length)
		speed = int(self._last_status.get("downloadSpeed", 0))
		if speed <= 0:
			return get_readable_time(0)
		secs = remain // max(1, speed)
		return get_readable_time(int(secs))

	@property
	def is_waiting(self) -> bool:
		self._update()
		return self._last_status.get("status") == "waiting"

	@property
	def is_paused(self) -> bool:
		self._update()
		return self._last_status.get("status") == "paused"

	@property
	def has_failed(self) -> bool:
		self._update()
		return self._last_status.get("status") == "error" or self._last_status.get("errorCode") not in (None, "0", 0)

	@property
	def connections(self) -> int:
		self._update()
		return int(self._last_status.get("connections", 0))

	@property
	def num_seeders(self) -> int:
		self._update()
		return int(self._last_status.get("numSeeders", 0))

	@property
	def dir(self) -> str:
		self._update()
		return self._last_status.get("dir", "")


class AioAria2API:
	def __init__(self, rpc_url: str, token: Optional[str] = None):
		self._rpc_url = rpc_url
		self._token = token or ""
		self._http = aioaria2.Aria2HttpClient(self._rpc_url, token=self._token)
		self._ws_thread = None

	def _run(self, coro):
		return asyncio.run(coro)

	def listen_to_notifications(self, threaded: bool = True, on_download_start: Optional[Callable] = None,
							  on_download_error: Optional[Callable] = None, on_download_pause: Optional[Callable] = None,
							  on_download_stop: Optional[Callable] = None, on_download_complete: Optional[Callable] = None):
		async def _runner():
			trigger = await aioaria2.Aria2WebsocketTrigger.new(self._rpc_url, token=self._token)

			def _wrap(cb: Callable):
				if cb is None:
					return None
				@aioaria2.run_sync
				def _inner(_trigger, data):
					gid = data.get("gid") if isinstance(data, dict) else None
					try:
						cb(self, gid)
					except Exception:
						pass
				return _inner

			if on_download_start:
				trigger.onDownloadStart(_wrap(on_download_start))
			if on_download_error:
				trigger.onDownloadError(_wrap(on_download_error))
			if on_download_pause:
				trigger.onDownloadPause(_wrap(on_download_pause))
			if on_download_stop:
				trigger.onDownloadStop(_wrap(on_download_stop))
			if on_download_complete:
				trigger.onDownloadComplete(_wrap(on_download_complete))

			await asyncio.Future()

		if threaded:
			import threading
			self._ws_thread = threading.Thread(target=lambda: asyncio.run(_runner()), daemon=True)
			self._ws_thread.start()
		else:
			self._run(_runner())

	def add_magnet(self, link: str, options: Optional[Dict[str, Any]] = None) -> _AddResult:
		try:
			gid = self._run(self._http.addUri([link], options or {}))
			status = self._run(self._http.tellStatus(gid)) or {}
			return _AddResult(gid=gid, dir=status.get("dir", ""), error_message="")
		except Exception as e:
			return _AddResult(gid="", dir="", error_message=str(e))

	def add_uris(self, uris: List[str], options: Optional[Dict[str, Any]] = None) -> _AddResult:
		try:
			gid = self._run(self._http.addUri(uris, options or {}))
			status = self._run(self._http.tellStatus(gid)) or {}
			return _AddResult(gid=gid, dir=status.get("dir", ""), error_message="")
		except Exception as e:
			return _AddResult(gid="", dir="", error_message=str(e))

	def get_download(self, gid: str) -> _AioAria2Download:
		return _AioAria2Download(self, gid)

	def get_downloads(self, gids: Iterable[str]) -> List[_AioAria2Download]:
		return [self.get_download(g) for g in gids]

	def pause(self, downloads: Iterable[_AioAria2Download]) -> None:
		for dl in downloads:
			gid = dl.gid if isinstance(dl, _AioAria2Download) else str(dl)
			try:
				self._run(self._http.pause(gid))
			except Exception:
				pass

	def remove(self, downloads: Iterable[_AioAria2Download]) -> None:
		for dl in downloads:
			gid = dl.gid if isinstance(dl, _AioAria2Download) else str(dl)
			try:
				self._run(self._http.remove(gid))
			except Exception:
				pass

	def changeOption(self, gid: str, options: Dict[str, Any]) -> None:
		"""Change options for a download"""
		try:
			self._run(self._http.changeOption(gid, options))
		except Exception:
			pass
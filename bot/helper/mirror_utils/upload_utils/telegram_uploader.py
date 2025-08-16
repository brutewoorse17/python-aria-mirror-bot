import logging
import threading
import time
import subprocess
import os

from pyrogram import Client
from pymediainfo import MediaInfo
from bot import LOGGER, TELEGRAM_API, TELEGRAM_HASH, USER_SESSION_STRING, UPLOAD_AS_VIDEO, USE_CUSTOM_THUMB, VIDEO_THUMB_PATH, TG_PART_SIZE_MB

logging.getLogger("pyrogram").setLevel(logging.WARNING)


def _get_video_duration_seconds(file_path: str) -> int:
    try:
        mi = MediaInfo.parse(file_path)
        for track in mi.tracks:
            if track.track_type == 'Video' and track.duration:
                return int(float(track.duration) / 1000)
    except Exception:
        pass
    # fallback to ffprobe
    try:
        out = subprocess.check_output([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', file_path
        ], stderr=subprocess.STDOUT)
        return int(float(out.decode().strip()))
    except Exception:
        return 0


class TelegramUploader:
    def __init__(self, name, listener, chat_id, reply_to_message_id=None):
        self.name = name
        self.__listener = listener
        self.__chat_id = chat_id
        self.__reply_to_message_id = reply_to_message_id
        self.__user_bot = Client(':memory:',
                                 api_id=TELEGRAM_API,
                                 api_hash=TELEGRAM_HASH,
                                 session_string=USER_SESSION_STRING)
        self.__user_bot.start()
        self.uploaded_bytes = 0
        self.__size = 0
        self.__start_time = None
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True
        try:
            self.__user_bot.stop_transmission()
        except Exception:
            pass

    def speed(self):
        try:
            return self.uploaded_bytes / max(1e-3, (time.time() - self.__start_time))
        except ZeroDivisionError:
            return 0

    def __on_progress(self, current, total):
        if self.is_cancelled:
            self.__listener.onUploadError('Cancelled by user!')
            try:
                self.__user_bot.stop_transmission()
            except Exception:
                pass
            return
        self.uploaded_bytes = current
        self.__size = total

    def __send_one(self, file_path: str, display_name: str):
        if UPLOAD_AS_VIDEO and (display_name.lower().endswith('.mp4') or display_name.lower().endswith('.mkv')):
            duration = _get_video_duration_seconds(file_path)
            thumb = VIDEO_THUMB_PATH if USE_CUSTOM_THUMB and VIDEO_THUMB_PATH else None
            self.__user_bot.send_video(
                chat_id=self.__chat_id,
                video=file_path,
                file_name=display_name,
                supports_streaming=True,
                duration=duration if duration > 0 else None,
                thumb=thumb,
                progress=self.__on_progress,
                progress_args=(),
                reply_to_message_id=self.__reply_to_message_id
            )
        else:
            self.__user_bot.send_document(
                chat_id=self.__chat_id,
                document=file_path,
                file_name=display_name,
                progress=self.__on_progress,
                progress_args=(),
                reply_to_message_id=self.__reply_to_message_id
            )

    def upload(self, file_path):
        try:
            self.__start_time = time.time()
            LOGGER.info(f"Uploading to Telegram: {file_path}")
            part_size = max(1, TG_PART_SIZE_MB) * 1024 * 1024
            file_size = os.path.getsize(file_path)
            if file_size <= part_size:
                self.__send_one(file_path, self.name)
            else:
                # split into parts and send sequentially
                base, ext = os.path.splitext(self.name)
                num_parts = (file_size + part_size - 1) // part_size
                with open(file_path, 'rb') as f:
                    idx = 1
                    bytes_sent_total = 0
                    while True:
                        if self.is_cancelled:
                            break
                        chunk = f.read(part_size)
                        if not chunk:
                            break
                        part_path = f"{file_path}.part{idx:03d}"
                        with open(part_path, 'wb') as pf:
                            pf.write(chunk)
                        display_name = f"{base}.part{idx:03d}{ext} ({idx}/{num_parts})"
                        try:
                            self.__send_one(part_path, display_name)
                            bytes_sent_total += len(chunk)
                        finally:
                            try:
                                os.remove(part_path)
                            except Exception:
                                pass
                        idx += 1
                # adjust uploaded bytes for status correctness
                self.uploaded_bytes = file_size
                self.__size = file_size
            if self.is_cancelled:
                return None
            self.__listener.onUploadComplete('')
            return True
        except Exception as e:
            LOGGER.error(str(e))
            self.__listener.onUploadError(str(e))
            return None
        finally:
            try:
                self.__user_bot.stop()
            except Exception:
                pass
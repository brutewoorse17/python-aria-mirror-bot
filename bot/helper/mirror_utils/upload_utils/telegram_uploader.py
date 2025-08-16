import logging
import threading
import time

from pyrogram import Client
from bot import LOGGER, TELEGRAM_API, TELEGRAM_HASH, USER_SESSION_STRING, bot
from bot.helper.ext_utils.bot_utils import should_update_status, get_readable_file_size, get_readable_time

logging.getLogger("pyrogram").setLevel(logging.WARNING)


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
        self._status_message = None

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

    def __format_status(self) -> str:
        percent = 0 if self.__size == 0 else self.uploaded_bytes * 100 / max(1, self.__size)
        try:
            eta_secs = (self.__size - self.uploaded_bytes) / max(1e-3, self.speed())
        except ZeroDivisionError:
            eta_secs = 0
        return (f"Uploading {self.name}\n"
                f"{round(percent, 2)}% of {get_readable_file_size(self.__size)} "
                f"at {get_readable_file_size(self.speed())}/s, ETA: {get_readable_time(int(eta_secs))}")

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
        if should_update_status(2.0):
            try:
                if self._status_message is None:
                    self._status_message = bot.send_message(self.__chat_id,
                                                             reply_to_message_id=self.__reply_to_message_id,
                                                             text=self.__format_status(),
                                                             parse_mode='HTML')
                else:
                    bot.edit_message_text(text=self.__format_status(),
                                          chat_id=self._status_message.chat.id,
                                          message_id=self._status_message.message_id,
                                          parse_mode='HTML')
            except Exception:
                pass

    def upload(self, file_path):
        try:
            self.__start_time = time.time()
            LOGGER.info(f"Uploading to Telegram: {file_path}")
            self.__user_bot.send_document(
                chat_id=self.__chat_id,
                document=file_path,
                file_name=self.name,
                progress=self.__on_progress,
                progress_args=(),
                reply_to_message_id=self.__reply_to_message_id
            )
            if self.is_cancelled:
                return None
            # Clear status message if present
            try:
                if self._status_message is not None:
                    bot.edit_message_text(text=f"Uploaded to Telegram: {self.name}",
                                          chat_id=self._status_message.chat.id,
                                          message_id=self._status_message.message_id,
                                          parse_mode='HTML')
            except Exception:
                pass
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
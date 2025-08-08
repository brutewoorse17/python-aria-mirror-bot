import logging
import threading
import time

from pyrogram import Client

from bot import LOGGER, TELEGRAM_API, TELEGRAM_HASH, USER_SESSION_STRING

logging.getLogger("pyrogram").setLevel(logging.WARNING)


class TelegramUploader:
    def __init__(self, name, listener, chat_id, reply_to_message_id=None):
        self.name = name
        self.__listener = listener
        self.__chat_id = chat_id
        self.__reply_to_message_id = reply_to_message_id
        self.__user_bot = Client(api_id=TELEGRAM_API,
                                 api_hash=TELEGRAM_HASH,
                                 session_name=USER_SESSION_STRING)
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
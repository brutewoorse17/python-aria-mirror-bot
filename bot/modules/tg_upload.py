import os
import pathlib
import subprocess
import threading

from telegram.ext import CommandHandler

from bot import Interval, LOGGER
from bot import application, DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, download_dict, download_dict_lock
from bot.helper.ext_utils import fs_utils, bot_utils
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.ext_utils.exceptions import NotSupportedExtractionArchive
from bot.helper.mirror_utils.download_utils.aria2_download import AriaDownloadHelper
from bot.helper.mirror_utils.download_utils.telegram_downloader import TelegramDownloadHelper
from bot.helper.mirror_utils.status_utils import listeners
from bot.helper.mirror_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_utils.status_utils.tar_status import TarStatus
from bot.helper.mirror_utils.status_utils.upload_status import UploadStatus
from bot.helper.mirror_utils.upload_utils.telegram_uploader import TelegramUploader
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import *

ariaDlManager = AriaDownloadHelper()
ariaDlManager.start_listener()


class TgUploadListener(listeners.MirrorListeners):
    def __init__(self, bot, update, isTar=False, tag=None, extract=False):
        super().__init__(bot, update)
        self.isTar = isTar
        self.tag = tag
        self.extract = extract

    def onDownloadStarted(self):
        pass

    def onDownloadProgress(self):
        pass

    def clean(self):
        try:
            Interval[0].cancel()
            del Interval[0]
            delete_all_messages()
        except IndexError:
            pass

    def onDownloadComplete(self):
        with download_dict_lock:
            LOGGER.info(f"Download completed: {download_dict[self.uid].name()}")
            download = download_dict[self.uid]
            name = download.name()
            size = download.size_raw()
            if name is None:
                name = os.listdir(f'{DOWNLOAD_DIR}{self.uid}')[0]
            m_path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        if self.isTar:
            download.is_archiving = True
            try:
                with download_dict_lock:
                    download_dict[self.uid] = TarStatus(name, m_path, size)
                path = fs_utils.tar(m_path)
            except FileNotFoundError:
                LOGGER.info('File to archive not found!')
                self.onUploadError('Internal error occurred!!')
                return
        elif self.extract:
            download.is_extracting = True
            try:
                path = fs_utils.get_base_name(m_path)
                LOGGER.info(
                    f"Extracting : {name} "
                )
                with download_dict_lock:
                    download_dict[self.uid] = ExtractStatus(name, m_path, size)
                archive_result = subprocess.run(["extract", m_path])
                if archive_result.returncode == 0:
                    threading.Thread(target=os.remove, args=(m_path,)).start()
                    LOGGER.info(f"Deleting archive : {m_path}")
                else:
                    LOGGER.warning('Unable to extract archive! Uploading anyway')
                    path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
                LOGGER.info(
                    f'got path : {path}'
                )

            except NotSupportedExtractionArchive:
                LOGGER.info("Not any valid archive, uploading file as it is.")
                path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        else:
            path = f'{DOWNLOAD_DIR}{self.uid}/{name}'

        # If it is a directory, try tarring before upload
        if os.path.isdir(path):
            try:
                path = fs_utils.tar(path)
                name = pathlib.PurePath(path).name
            except Exception:
                self.onUploadError('Cannot upload directories to Telegram')
                return
        else:
            name = pathlib.PurePath(path).name

        # Prepare Telegram uploader and status
        if size == 0:
            size = fs_utils.get_path_size(path)
        uploader = TelegramUploader(name, self, self.update.effective_chat.id, self.update.message.message_id)
        upload_status = UploadStatus(uploader, size, self)
        with download_dict_lock:
            download_dict[self.uid] = upload_status
        update_all_messages()

        # Start upload (blocking until complete)
        uploader.upload(path)

    def onDownloadError(self, error):
        error = error.replace('<', ' ').replace('>', ' ')
        LOGGER.info(self.update.effective_chat.id)
        with download_dict_lock:
            try:
                download = download_dict[self.uid]
                del download_dict[self.uid]
                LOGGER.info(f"Deleting folder: {download.path()}")
                fs_utils.clean_download(download.path())
                LOGGER.info(str(download_dict))
            except Exception as e:
                LOGGER.error(str(e))
                pass
            count = len(download_dict)
        if self.message.from_user.username:
            uname = f"@{self.message.from_user.username}"
        else:
            uname = f'<a href="tg://user?id={self.message.from_user.id}">{self.message.from_user.first_name}</a>'
        msg = f"{uname} your download has been stopped due to: {error}"
        try:
            self.bot.send_message(self.update.effective_chat.id, reply_to_message_id=self.update.message.message_id, text=msg, parse_mode='HTML')
        except Exception:
            pass
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadStarted(self):
        pass

    def onUploadProgress(self):
        pass

    def onUploadComplete(self, _link: str):
        with download_dict_lock:
            try:
                fs_utils.clean_download(f'{DOWNLOAD_DIR}{self.uid}')
            except FileNotFoundError:
                pass
            try:
                del download_dict[self.uid]
            except KeyError:
                pass
            count = len(download_dict)
        msg = f"Uploaded to Telegram: {self.message.message_id}"
        if self.tag is not None:
            msg += f'\ncc: @{self.tag}'
        try:
            self.bot.send_message(self.update.effective_chat.id, reply_to_message_id=self.update.message.message_id, text=msg, parse_mode='HTML')
        except Exception:
            pass
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadError(self, error):
        e_str = error.replace('<', '').replace('>', '')
        with download_dict_lock:
            try:
                fs_utils.clean_download(f'{DOWNLOAD_DIR}{self.uid}')
            except FileNotFoundError:
                pass
            try:
                del download_dict[self.message.message_id]
            except KeyError:
                pass
            count = len(download_dict)
        try:
            self.bot.send_message(self.update.effective_chat.id, reply_to_message_id=self.update.message.message_id, text=e_str, parse_mode='HTML')
        except Exception:
            pass
        if count == 0:
            self.clean()
        else:
            update_all_messages()


async def tgupload(update, context):
    message_args = update.message.text.split(' ')
    try:
        link = message_args[1]
    except IndexError:
        link = ''
    link = link.strip()
    reply_to = update.message.reply_to_message
    if reply_to is not None:
        file = None
        tag = reply_to.from_user.username
        media_array = [reply_to.document, reply_to.video, reply_to.audio]
        for i in media_array:
            if i is not None:
                file = i
                break

        if len(link) == 0:
            if file is not None:
                if file.mime_type != "application/x-bittorrent":
                    listener = TgUploadListener(context.bot, update, False, tag, False)
                    tg_downloader = TelegramDownloadHelper(listener)
                    tg_downloader.add_download(reply_to, f'{DOWNLOAD_DIR}{listener.uid}/')
                    await sendStatusMessage(update, context)
                    if len(Interval) == 0:
                        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))
                    return
                else:
                    link = file.get_file().file_path
    else:
        tag = None
    if not bot_utils.is_url(link) and not bot_utils.is_magnet(link):
        await sendMessage('No download source provided', context)
        return

    listener = TgUploadListener(context.bot, update, False, tag, False)
    ariaDlManager.add_download(link, f'{DOWNLOAD_DIR}{listener.uid}/', listener)
    await sendStatusMessage(update, context)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))


tg_upload_handler = CommandHandler(BotCommands.TgUploadCommand, tgupload,
                                   filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
application.add_handler(tg_upload_handler)
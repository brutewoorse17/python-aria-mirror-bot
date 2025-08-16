import requests
from telegram.ext import CommandHandler

from bot import Interval, INDEX_URL, LOGGER, MEGA_KEY
from bot import application, DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, download_dict, download_dict_lock
from bot.helper.ext_utils import fs_utils, bot_utils
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException, NotSupportedExtractionArchive
from bot.helper.mirror_utils.download_utils.aria2_download import AriaDownloadHelper
from bot.helper.mirror_utils.download_utils.direct_link_generator import direct_link_generator
from bot.helper.mirror_utils.download_utils.telegram_downloader import TelegramDownloadHelper
from bot.helper.mirror_utils.status_utils import listeners
from bot.helper.mirror_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_utils.status_utils.tar_status import TarStatus
from bot.helper.mirror_utils.status_utils.upload_status import UploadStatus
from bot.helper.mirror_utils.upload_utils import gdriveTools
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import *
from bot.helper.mirror_utils.download_utils.mega_download import MegaDownloader
import pathlib
import os
import subprocess
import threading

ariaDlManager = AriaDownloadHelper()
ariaDlManager.start_listener()


class MirrorListener(listeners.MirrorListeners):
    def __init__(self, bot, update, isTar=False, tag=None, extract=False):
        super().__init__(bot, update)
        self.isTar = isTar
        self.tag = tag
        self.extract = extract

    def onDownloadStarted(self):
        pass

    def onDownloadProgress(self):
        # We are handling this on our own!
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
            if name is None: # when pyrogram's media.file_name is of NoneType
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
        up_name = pathlib.PurePath(path).name
        LOGGER.info(f"Upload Name : {up_name}")
        drive = gdriveTools.GoogleDriveHelper(up_name, self)
        if size == 0:
            size = fs_utils.get_path_size(m_path)
        upload_status = UploadStatus(drive, size, self)
        with download_dict_lock:
            download_dict[self.uid] = upload_status
        update_all_messages()
        drive.upload(up_name)

    def onDownloadError(self, error):
        error = error.replace('<', ' ')
        error = error.replace('>', ' ')
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
        from bot.helper.telegram_helper.message_utils import send_message_async
        send_message_async(self.update.effective_chat.id, self.update.message.message_id, msg, parse_mode='HTML')
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadStarted(self):
        pass

    def onUploadProgress(self):
        pass

    def onUploadComplete(self, link: str):
        with download_dict_lock:
            msg = f'<a href="{link}">{download_dict[self.uid].name()}</a> ({download_dict[self.uid].size()})'
            LOGGER.info(f'Done Uploading {download_dict[self.uid].name()}')
            if INDEX_URL is not None:
                share_url = requests.utils.requote_uri(f'{INDEX_URL}/{download_dict[self.uid].name()}')
                if os.path.isdir(f'{DOWNLOAD_DIR}/{self.uid}/{download_dict[self.uid].name()}'):
                    share_url += '/'
                msg += f'\n\n Shareable link: <a href="{share_url}">here</a>'
            if self.tag is not None:
                msg += f'\ncc: @{self.tag}'
            try:
                fs_utils.clean_download(download_dict[self.uid].path())
            except FileNotFoundError:
                pass
            del download_dict[self.uid]
            count = len(download_dict)
        from bot.helper.telegram_helper.message_utils import send_message_async
        send_message_async(self.update.effective_chat.id, self.update.message.message_id, msg, parse_mode='HTML')
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadError(self, error):
        e_str = error.replace('<', '').replace('>', '')
        with download_dict_lock:
            try:
                fs_utils.clean_download(download_dict[self.uid].path())
            except FileNotFoundError:
                pass
            del download_dict[self.message.message_id]
            count = len(download_dict)
        from bot.helper.telegram_helper.message_utils import send_message_async
        send_message_async(self.update.effective_chat.id, self.update.message.message_id, e_str, parse_mode='HTML')
        if count == 0:
            self.clean()
        else:
            update_all_messages()


async def mirror(update, context):
    message_args = update.message.text.split(' ')
    try:
        link = message_args[1]
    except IndexError:
        link = ''
    LOGGER.info(link)
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
                    listener = MirrorListener(context.bot, update, False, tag, False)
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

    try:
        link = direct_link_generator(link)
    except DirectDownloadLinkException as e:
        LOGGER.info(f'{link}: {e}')
    listener = MirrorListener(context.bot, update, False, tag, False)
    if bot_utils.is_mega_link(link) and MEGA_KEY is not None:
        mega_dl = MegaDownloader(listener)
        mega_dl.add_download(link, f'{DOWNLOAD_DIR}{listener.uid}/')
    else:
        ariaDlManager.add_download(link, f'{DOWNLOAD_DIR}{listener.uid}/', listener)
    await sendStatusMessage(update, context)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))


async def tar_mirror(update, context):
    await mirror(update, context)


async def unzip_mirror(update, context):
    message_args = update.message.text.split(' ')
    try:
        link = message_args[1]
    except IndexError:
        link = ''
    reply_to = update.message.reply_to_message
    tag = reply_to.from_user.username if reply_to is not None else None
    listener = MirrorListener(context.bot, update, False, tag, True)
    if not bot_utils.is_url(link) and not bot_utils.is_magnet(link):
        await sendMessage('No download source provided', context)
        return
    ariaDlManager.add_download(link, f'{DOWNLOAD_DIR}{listener.uid}/', listener)
    await sendStatusMessage(update, context)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))


mirror_handler = CommandHandler(BotCommands.MirrorCommand, mirror,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
tar_mirror_handler = CommandHandler(BotCommands.TarMirrorCommand, tar_mirror,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
unzip_mirror_handler = CommandHandler(BotCommands.UnzipMirrorCommand, unzip_mirror,
                                      filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
application.add_handler(mirror_handler)
application.add_handler(tar_mirror_handler)
application.add_handler(unzip_mirror_handler)

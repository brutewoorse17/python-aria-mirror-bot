from telegram.ext import CommandHandler
from telegram import Bot, Update
from bot import Interval, DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, application, LOGGER
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.telegram_helper.message_utils import update_all_messages, sendMessage, sendStatusMessage
from .mirror import MirrorListener, validate_filename
from bot.helper.mirror_utils.download_utils.youtube_dl_download_helper import YoutubeDLHelper
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
import threading


def _watch(bot: Bot, update: Update, args: list, isTar=False):
    try:
        link = args[0]
    except IndexError:
        msg = f"/{BotCommands.WatchCommand} [yt_dl supported link] [quality] [filename] to mirror with youtube_dl.\n\n"
        msg += "Example of quality :- audio, 144, 360, 720, 1080.\nNote :- Quality is optional\n"
        msg += "Example of filename: /watch <link> <quality> <filename> or /watch <filename> <link> <quality>"
        # Legacy sync util used here
        from bot.helper.telegram_helper.message_utils import bot as sync_bot
        sync_bot.send_message(update.effective_chat.id, reply_to_message_id=update.message.message_id, text=msg, parse_mode='HTML')
        return
    
    # Check for custom filename
    custom_filename = None
    if len(args) > 2:
        # Check if the second argument is a quality or filename
        if args[1] == "audio" or args[1].isdigit():
            # Format: /watch <link> <quality> <filename>
            try:
                qual = args[1]
                if qual != "audio":
                    qual = f'best[height<={qual}]/bestvideo[height<={qual}]+bestaudio'
                custom_filename = ' '.join(args[2:])
            except IndexError:
                qual = "best/bestvideo+bestaudio"
        else:
            # Format: /watch <filename> <link> <quality>
            custom_filename = args[0]
            link = args[1]
            try:
                qual = args[2]
                if qual != "audio":
                    qual = f'best[height<={qual}]/bestvideo[height<={qual}]+bestaudio'
            except IndexError:
                qual = "best/bestvideo+bestaudio"
    else:
        try:
            qual = args[1]
            if qual != "audio":
                qual = f'best[height<={qual}]/bestvideo[height<={qual}]+bestaudio'
        except IndexError:
            qual = "best/bestvideo+bestaudio"
    
    # Validate custom filename if provided
    if custom_filename:
        from .mirror import validate_filename
        is_valid, error_msg = validate_filename(custom_filename)
        if not is_valid:
            msg = f"❌ Invalid filename: {error_msg}"
            from bot.helper.telegram_helper.message_utils import bot as sync_bot
            sync_bot.send_message(update.effective_chat.id, reply_to_message_id=update.message.message_id, text=msg, parse_mode='HTML')
            return
    
    reply_to = update.message.reply_to_message
    if reply_to is not None:
        tag = reply_to.from_user.username
    else:
        tag = None

    listener = MirrorListener(bot, update, isTar, tag)
    if custom_filename:
        listener.custom_filename = custom_filename
    
    ydl = YoutubeDLHelper(listener)
    threading.Thread(target=ydl.add_download,args=(link, f'{DOWNLOAD_DIR}{listener.uid}', qual)).start()
    from bot.helper.telegram_helper.message_utils import bot as sync_bot
    sync_bot.send_message(update.effective_chat.id, reply_to_message_id=update.message.message_id, text="Starting...")
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))


async def watchTar(update, context):
    _watch(context.bot, update, context.args, True)


def watch(update, context):
    _watch(context.bot, update, context.args)


mirror_handler = CommandHandler(BotCommands.WatchCommand, watch,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
tar_mirror_handler = CommandHandler(BotCommands.TarWatchCommand, watchTar,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
# Handlers are now registered in __main__.py

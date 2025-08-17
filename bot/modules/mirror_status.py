from telegram.ext import CommandHandler
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *
from bot import application, status_reply_dict, DOWNLOAD_STATUS_UPDATE_INTERVAL, status_reply_dict_lock, bot
from time import sleep
from bot.helper.ext_utils.bot_utils import get_readable_message
from telegram.error import BadRequest
import threading

async def mirror_status(update, context):
    with status_reply_dict_lock:
        if update.message.chat.id in list(status_reply_dict.keys()):
            try:
                message_obj, _ = status_reply_dict[update.message.chat.id]
                if message_obj:  # Only delete if message_obj is not None
                    await deleteMessage(context, message_obj)
                del status_reply_dict[update.message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))
                del status_reply_dict[update.message.chat.id]
        
        message = await sendMessage(get_readable_message(), context, update)
        # Only store in status_reply_dict if message was sent successfully
        if message is not None:
            status_reply_dict[update.message.chat.id] = (message, get_readable_message())
        else:
            LOGGER.error(f"Failed to send status message to chat {update.message.chat.id}")


stats_handler = CommandHandler(BotCommands.StatusCommand, mirror_status,
                               filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
application.add_handler(stats_handler)

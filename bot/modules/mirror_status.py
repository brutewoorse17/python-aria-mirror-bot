from telegram.ext import CommandHandler
from bot import application, status_reply_dict, DOWNLOAD_STATUS_UPDATE_INTERVAL, status_reply_dict_lock, bot
from bot.helper.telegram_helper.message_utils import *
from time import sleep
from bot.helper.ext_utils.bot_utils import get_readable_message
from telegram.error import BadRequest
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
import threading

async def mirror_status(update,context):
    message = get_readable_message()
    if len(message) == 0:
        message = "No active downloads"
        reply_message = await sendMessage(message, context)
        threading.Thread(target=auto_delete_message, args=(bot, update.message, reply_message)).start()
        return
    index = update.effective_chat.id
    with status_reply_dict_lock:
        if index in status_reply_dict.keys():
            try:
                bot.delete_message(chat_id=status_reply_dict[index].chat.id,
                                   message_id=status_reply_dict[index].message_id)
            except Exception:
                pass
            del status_reply_dict[index]
    await sendStatusMessage(update,context)
    await deleteMessage(context,update.message)


mirror_status_handler = CommandHandler(BotCommands.StatusCommand, mirror_status,
                                       filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
application.add_handler(mirror_status_handler)

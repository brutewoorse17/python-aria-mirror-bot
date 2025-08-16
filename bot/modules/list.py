from bot import LOGGER, application
from bot.helper.telegram_helper.message_utils import auto_delete_message, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
import threading
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from telegram.ext import CommandHandler


async def list_drive(update, context):
    args = update.message.text.split(' ')
    search = ' '.join(args[1:]).strip()
    if not search:
        reply_message = await sendMessage('No search term provided', context)
        threading.Thread(target=auto_delete_message, args=(context.bot, update.message, reply_message)).start()
        return
    LOGGER.info(f"Searching: {search}")
    gdrive = GoogleDriveHelper()
    msg = gdrive.drive_list(search)
    if msg:
        reply_message = await sendMessage(msg, context)
    else:
        reply_message = await sendMessage('No result found', context)
    threading.Thread(target=auto_delete_message, args=(context.bot, update.message, reply_message)).start()


list_handler = CommandHandler(BotCommands.ListCommand, list_drive,filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
application.add_handler(list_handler)

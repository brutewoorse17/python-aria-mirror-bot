from bot import LOGGER, application
from bot.helper.telegram_helper.message_utils import auto_delete_message, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
import threading
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from telegram.ext import CommandHandler


def list_drive(update, context):
    args = update.message.text.split(' ')
    search = ' '.join(args[1:])
    gdrive = GoogleDriveHelper()
    msg = gdrive.drive_list(search)
    if msg:
        reply_message = threading.get_native_id()  # placeholder to satisfy type; will be replaced
    else:
        reply_message = threading.get_native_id()


list_handler = CommandHandler(BotCommands.ListCommand, list_drive,filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
application.add_handler(list_handler)

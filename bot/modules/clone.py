from telegram.ext import CommandHandler
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import new_thread
from bot import application


@new_thread
async def clone_drive(update, context):
    args = update.message.text.split(' ')
    try:
        link = args[1]
    except IndexError:
        link = ''
    if link:
        gdrive = GoogleDriveHelper()
        msg = await sendMessage(f"Cloning: <code>{link}</code>", context, update)
        result = gdrive.clone(link)
        await sendMessage(result,context, update)
    else:
        await sendMessage("Provide G-Drive Shareable Link to Clone.",context, update)


clone_handler = CommandHandler(BotCommands.CloneCommand, clone_drive, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
application.add_handler(clone_handler)
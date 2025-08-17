from telegram.ext import CommandHandler
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import *
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import new_thread
from bot import application


@new_thread
async def cloneNode(update,context):
    args = update.message.text.split(" ",maxsplit=1)
    if len(args) > 1:
        link = args[1]
        msg = await sendMessage(f"Cloning: <code>{link}</code>", context)
        gd = GoogleDriveHelper()
        result = gd.clone(link)
        await deleteMessage(context,msg)
        await sendMessage(result,context)
    else:
        await sendMessage("Provide G-Drive Shareable Link to Clone.",context)

clone_handler = CommandHandler(BotCommands.CloneCommand,cloneNode,filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
# Handler is now registered in __main__.py
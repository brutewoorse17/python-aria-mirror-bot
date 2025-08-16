from bot import LOGGER, application
from bot.helper.telegram_helper.message_utils import auto_delete_message, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
import threading
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from telegram.ext import CommandHandler
from telegraph import Telegraph

telegraph = Telegraph()
telegraph.create_account(short_name="mirrorbot")


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
    if not msg:
        reply_message = await sendMessage('No result found', context)
        threading.Thread(target=auto_delete_message, args=(context.bot, update.message, reply_message)).start()
        return
    lines = msg.strip().split('\n')
    if len(lines) > 10 or len(msg) > 3500:
        # Build Telegraph content as simple HTML
        html_content = "<h3>Search results for: {}</h3><hr/>".format(search)
        for line in lines:
            html_content += "<p>{}</p>".format(line)
        try:
            page = telegraph.create_page(title=f"Results: {search}", html_content=html_content)
            url = "https://telegra.ph/" + page["path"]
            reply_message = await sendMessage(f"Results: {url}", context)
        except Exception as e:
            LOGGER.error(str(e))
            reply_message = await sendMessage(msg, context)
    else:
        reply_message = await sendMessage(msg, context)
    threading.Thread(target=auto_delete_message, args=(context.bot, update.message, reply_message)).start()


list_handler = CommandHandler(BotCommands.ListCommand, list_drive,filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
application.add_handler(list_handler)

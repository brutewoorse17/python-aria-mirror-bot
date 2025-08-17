import shutil, psutil
import signal
import pickle

from os import execl, path, remove
from sys import executable
import time

from telegram.ext import CommandHandler, Application, filters
from bot import application, botStartTime, LOGGER
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from .modules import authorize, list, cancel_mirror, mirror_status, mirror, clone, watch
from .modules import settings
from .modules import rename


async def stats(update, context):
    currentTime = get_readable_time((time.time() - botStartTime))
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    stats = f'Bot Uptime: {currentTime}\n' \
            f'Total disk space: {total}\n' \
            f'Used: {used}\n' \
            f'Free: {free}\n' \
            f'CPU: {cpuUsage}%\n' \
            f'RAM: {memory}%'
    await sendMessage(stats, context)


async def start(update, context):
    start_string = f'''
This is a bot which can mirror all your links to Google drive!
Type /{BotCommands.HelpCommand} to get a list of available commands
'''
    await sendMessage(start_string, context)


async def restart(update, context):
    restart_message = await sendMessage("Restarting, Please wait!", context)
    # Save restart message object in order to reply to it after restarting
    fs_utils.clean_all()
    with open('restart.pickle', 'wb') as status:
        pickle.dump(restart_message, status)
    execl(executable, executable, "-m", "bot")


async def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = await sendMessage("Starting Ping", context)
    end_time = int(round(time.time() * 1000))
    await editMessage(f'{end_time - start_time} ms', reply, context)


async def log(update, context):
    await sendLogFile(context)


async def bot_help(update, context):
    help_string = f'''
/{BotCommands.HelpCommand}: To get this message

/{BotCommands.MirrorCommand} [link] [filename] or [filename] [link]: Start mirroring the link to google drive with optional custom filename

/{BotCommands.UnzipMirrorCommand} [link] [filename] or [filename] [link] : starts mirroring and if downloaded file is any archive , extracts it to google drive with optional custom filename

/{BotCommands.TarMirrorCommand} [link] [filename] or [filename] [link]: start mirroring and upload the archived (.tar) version of the download with optional custom filename

/{BotCommands.WatchCommand} [youtube-dl supported link] [quality] [filename] or [filename] [link] [quality]: Mirror through youtube-dl with optional custom filename. Click /{BotCommands.WatchCommand} for more help.

/{BotCommands.TarWatchCommand} [youtube-dl supported link] [quality] [filename] or [filename] [link] [quality]: Mirror through youtube-dl and tar before uploading with optional custom filename

/{BotCommands.CancelMirror} : Reply to the message by which the download was initiated and that download will be cancelled

/{BotCommands.StatusCommand}: Shows a status of all the downloads

/{BotCommands.ListCommand} [search term]: Searches the search term in the Google drive, if found replies with the link

/{BotCommands.StatsCommand}: Show Stats of the machine the bot is hosted on

/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Can only be invoked by owner of the bot)

/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports

/{BotCommands.TgUploadCommand} [download_url] (or reply to a file): Download and upload the file back to Telegram

/{BotCommands.RenameCommand} [gid] [new_name] or reply to a message with /{BotCommands.RenameCommand} [new_name]: Rename a torrent download

/{BotCommands.ListTorrentsCommand}: List all active torrent downloads

📝 <b>Examples:</b>
• <code>/{BotCommands.MirrorCommand} https://example.com/file.zip My Custom File</code>
• <code>/{BotCommands.MirrorCommand} My Custom File https://example.com/file.zip</code>
• <code>/{BotCommands.WatchCommand} https://youtube.com/watch?v=abc 720 My Video</code>
• <code>/{BotCommands.WatchCommand} My Video https://youtube.com/watch?v=abc 720</code>
• <code>/{BotCommands.RenameCommand} abc123 New Torrent Name</code>

'''
    await sendMessage(help_string, context)


def main():
    fs_utils.start_cleanup()
    # Check if the bot is restarting
    if path.exists('restart.pickle'):
        with open('restart.pickle', 'rb') as status:
            restart_message = pickle.load(status)
        restart_message.edit_text("Restarted Successfully!")
        remove('restart.pickle')

    app = application
    
    # Register all command handlers
    app.add_handler(CommandHandler(BotCommands.StartCommand, start,
                                   filters=CustomFilters.authorized_chat | CustomFilters.authorized_user))
    app.add_handler(CommandHandler(BotCommands.PingCommand, ping,
                                   filters=CustomFilters.authorized_chat | CustomFilters.authorized_user))
    app.add_handler(CommandHandler(BotCommands.RestartCommand, restart,
                                   filters=CustomFilters.owner_filter))
    app.add_handler(CommandHandler(BotCommands.HelpCommand,
                                   bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user))
    app.add_handler(CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user))
    app.add_handler(CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter))
    
    # Register module handlers
    # Telegram upload command handler
    from .modules.tg_upload import tg_upload_handler
    app.add_handler(tg_upload_handler)
    
    # Rename command handlers
    from .modules.rename import rename_handler, list_torrents_handler
    app.add_handler(rename_handler)
    app.add_handler(list_torrents_handler)
    
    # Mirror command handlers
    from .modules.mirror import mirror_handler, tar_mirror_handler, unzip_mirror_handler
    app.add_handler(mirror_handler)
    app.add_handler(tar_mirror_handler)
    app.add_handler(unzip_mirror_handler)
    
    # Watch command handlers
    from .modules.watch import mirror_handler as watch_handler, tar_mirror_handler as tar_watch_handler
    app.add_handler(watch_handler)
    app.add_handler(tar_watch_handler)
    
    # Other command handlers
    from .modules.list import list_handler
    app.add_handler(list_handler)
    
    from .modules.clone import clone_handler
    app.add_handler(clone_handler)
    
    from .modules.cancel_mirror import cancel_mirror_handler, cancel_all_handler
    app.add_handler(cancel_mirror_handler)
    app.add_handler(cancel_all_handler)
    
    from .modules.mirror_status import mirror_status_handler
    app.add_handler(mirror_status_handler)
    
    from .modules.settings import settings_handler, settings_cb_handler
    app.add_handler(settings_handler)
    app.add_handler(settings_cb_handler)
    
    from .modules.authorize import authorize_handler, unauthorize_handler
    app.add_handler(authorize_handler)
    app.add_handler(unauthorize_handler)

    app.run_polling()
    LOGGER.info("Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)


main()

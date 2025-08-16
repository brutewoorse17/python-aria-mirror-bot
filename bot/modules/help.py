import os
from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

from bot import application
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.telegram_helper.help_messages import MEGA_JD_HELP, BOT_HELP, COMMAND_EXAMPLES

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    message_args = update.message.text.split(' ')
    
    if len(message_args) > 1:
        command = message_args[1].lower()
        
        if command == 'megajd':
            await sendMessage(MEGA_JD_HELP, context)
        elif command == 'examples':
            await sendMessage(COMMAND_EXAMPLES, context)
        else:
            await sendMessage(f"Unknown help topic: {command}\nUse /help for general help", context)
    else:
        await sendMessage(BOT_HELP, context)

async def mega_jd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /megajdhelp command specifically for Mega.nz JDownloader"""
    await sendMessage(MEGA_JD_HELP, context)

async def examples_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /examples command for command examples"""
    await sendMessage(COMMAND_EXAMPLES, context)

# Add new help commands to BotCommands
BotCommands.HelpCommand = 'help'
BotCommands.MegaJDownloaderHelpCommand = 'megajdhelp'
BotCommands.ExamplesCommand = 'examples'

# Register handlers
help_handler = CommandHandler(
    BotCommands.HelpCommand, 
    help_command,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user
)

mega_jd_help_handler = CommandHandler(
    BotCommands.MegaJDownloaderHelpCommand, 
    mega_jd_help,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user
)

examples_handler = CommandHandler(
    BotCommands.ExamplesCommand, 
    examples_help,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user
)

# Add handlers to application
application.add_handler(help_handler)
application.add_handler(mega_jd_help_handler)
application.add_handler(examples_handler)
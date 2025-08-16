from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

from bot import application
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage

START_MESSAGE = """
🚀 **Welcome to Mirror Bot with Mega.nz JDownloader Integration!**

🤖 **What I can do:**
• Download files from various sources and upload to Google Drive
• **NEW!** Download Mega.nz files using JDownloader for reliable downloads
• Mirror Telegram files to Google Drive
• Download YouTube videos
• Clone Google Drive files

⭐ **New Mega.nz JDownloader Commands:**
• `/megajd <mega_link>` - Download Mega.nz files using JDownloader
• `/megajdstatus` - Check JDownloader status
• `/megajdhelp` - Detailed help for Mega.nz downloads

📚 **Other Commands:**
• `/help` - Show all available commands
• `/help megajd` - Mega.nz JDownloader specific help
• `/examples` - Command usage examples
• `/mirror <link>` - Regular file downloads
• `/status` - Check download progress

🔧 **Setup Required for Mega.nz:**
1. Create `config.json` with your MyJDownloader credentials
2. Ensure JDownloader is running on your device
3. Have a MyJDownloader account

💡 **Why JDownloader for Mega.nz?**
• Reliable downloads with resume support
• Better handling of large files
• Progress monitoring and error recovery
• Automatic retry on failures

Use `/help` for detailed command information!
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await sendMessage(START_MESSAGE, context)

# Register handler
start_handler = CommandHandler(
    BotCommands.StartCommand, 
    start_command,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user
)

# Add handler to application
application.add_handler(start_handler)
import re
from telegram.ext import CommandHandler

from bot import LOGGER, download_dict, download_dict_lock
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import *
from bot.helper.ext_utils.bot_utils import getDownloadByGid


def get_active_torrents():
    """Get list of active torrent downloads"""
    active_torrents = []
    with download_dict_lock:
        for message_id, download in download_dict.items():
            if hasattr(download, 'is_torrent') and download.is_torrent():
                status = download.status()
                if status not in ['Uploading', 'Archiving', 'Extracting']:
                    active_torrents.append({
                        'message_id': message_id,
                        'gid': download.gid(),
                        'name': download.name(),
                        'status': status
                    })
    return active_torrents


def validate_torrent_name(name):
    """Validate torrent name for invalid characters"""
    import re
    # Remove or replace invalid characters for file/directory names
    invalid_chars = r'[<>:"/\\|?*]'
    if re.search(invalid_chars, name):
        return False, "Torrent name contains invalid characters: < > : \" / \\ | ? *"
    
    if len(name.strip()) == 0:
        return False, "Torrent name cannot be empty"
    
    if len(name) > 255:
        return False, "Torrent name is too long (max 255 characters)"
    
    return True, ""


async def rename_torrent(update, context):
    """
    Rename a torrent download
    Usage: /rename <gid> <new_name> or reply to a message with /rename <new_name>
    """
    message_args = update.message.text.split(' ')
    
    if len(message_args) < 2:
        # Show help and list active torrents
        active_torrents = get_active_torrents()
        if not active_torrents:
            await sendMessage("No active torrent downloads found.\n\nUsage: /rename <gid> <new_name> or reply to a message with /rename <new_name>", context)
            return
        
        help_text = "Active torrent downloads:\n\n"
        for torrent in active_torrents:
            help_text += f"📁 <b>{torrent['name']}</b>\n"
            help_text += f"🆔 GID: <code>{torrent['gid']}</code>\n"
            help_text += f"📊 Status: {torrent['status']}\n\n"
        
        help_text += "💡 <b>Usage:</b>\n"
        help_text += "• <code>/rename {gid} {new_name}</code> - Rename by GID\n"
        help_text += "• Reply to a message with <code>/rename {new_name}</code> - Rename by reply\n\n"
        help_text += "📝 <b>Examples:</b>\n"
        help_text += "• <code>/rename abc123 My New Torrent Name</code>\n"
        help_text += "• Reply to a torrent message with <code>/rename Better Name</code>"
        
        await sendMessage(help_text, context, parse_mode='HTML')
        return
    
    reply_to = update.message.reply_to_message
    
    if reply_to is not None:
        # If replying to a message, try to find the download by message ID
        message_id = reply_to.message_id
        with download_dict_lock:
            if message_id in download_dict:
                download = download_dict[message_id]
                if hasattr(download, 'rename_torrent'):
                    if not download.is_torrent():
                        await sendMessage("This download is not a torrent. Only torrent downloads can be renamed.", context)
                        return
                    
                    new_name = ' '.join(message_args[1:])
                    if len(new_name.strip()) == 0:
                        await sendMessage("Please provide a valid name for the torrent.", context)
                        return
                    
                    # Validate torrent name
                    is_valid, error_msg = validate_torrent_name(new_name)
                    if not is_valid:
                        await sendMessage(f"❌ Invalid torrent name: {error_msg}", context)
                        return
                    
                    # Check if download is still active
                    if hasattr(download, 'status'):
                        status = download.status()
                        if status in ['Uploading', 'Archiving', 'Extracting']:
                            await sendMessage("Cannot rename torrent while it's being processed.", context)
                            return
                    
                    if download.rename_torrent(new_name):
                        current_name = download.name()
                        await sendMessage(f"✅ Successfully renamed torrent from <code>{current_name}</code> to <code>{new_name}</code>", context, parse_mode='HTML')
                    else:
                        await sendMessage("❌ Failed to rename torrent. Make sure it's an active torrent download.", context)
                else:
                    await sendMessage("This download doesn't support renaming.", context)
            else:
                await sendMessage("No active download found for this message.", context)
    else:
        # If not replying, expect gid and new name
        if len(message_args) < 3:
            await sendMessage("Usage: /rename <gid> <new_name> or reply to a message with /rename <new_name>", context)
            return
        
        try:
            gid = message_args[1]
            new_name = ' '.join(message_args[2:])
            
            if len(new_name.strip()) == 0:
                await sendMessage("Please provide a valid name for the torrent.", context)
                return
            
            # Validate torrent name
            is_valid, error_msg = validate_torrent_name(new_name)
            if not is_valid:
                await sendMessage(f"❌ Invalid torrent name: {error_msg}", context)
                return

            # Find download by GID
            download = getDownloadByGid(gid)
            if download and hasattr(download, 'rename_torrent'):
                if not download.is_torrent():
                    await sendMessage("This download is not a torrent. Only torrent downloads can be renamed.", context)
                    return
                
                # Check if download is still active
                if hasattr(download, 'status'):
                    status = download.status()
                    if status in ['Uploading', 'Archiving', 'Extracting']:
                        await sendMessage("Cannot rename torrent while it's being processed.", context)
                        return
                
                if download.rename_torrent(new_name):
                    current_name = download.name()
                    await sendMessage(f"✅ Successfully renamed torrent from <code>{current_name}</code> to <code>{new_name}</code>", context, parse_mode='HTML')
                else:
                    await sendMessage("❌ Failed to rename torrent. Make sure it's an active torrent download.", context)
            else:
                await sendMessage("No active download found with the specified GID.", context)
        except Exception as e:
            LOGGER.error(f"Error in rename command: {e}")
            await sendMessage("An error occurred while trying to rename the torrent.", context)


# Command handler
rename_handler = CommandHandler(BotCommands.RenameCommand, rename_torrent,
                               filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)

async def list_torrents(update, context):
    """List all active torrent downloads"""
    active_torrents = get_active_torrents()
    
    if not active_torrents:
        await sendMessage("📭 No active torrent downloads found.", context)
        return
    
    torrent_list = "📋 <b>Active Torrent Downloads:</b>\n\n"
    for i, torrent in enumerate(active_torrents, 1):
        torrent_list += f"<b>{i}.</b> 📁 <b>{torrent['name']}</b>\n"
        torrent_list += f"🆔 GID: <code>{torrent['gid']}</code>\n"
        torrent_list += f"📊 Status: {torrent['status']}\n\n"
    
    torrent_list += "💡 <b>To rename a torrent:</b>\n"
    torrent_list += "• Use <code>/rename {gid} {new_name}</code>\n"
    torrent_list += "• Or reply to a message with <code>/rename {new_name}</code>\n\n"
    torrent_list += "📝 <b>Examples:</b>\n"
    torrent_list += "• <code>/rename abc123 My New Torrent Name</code>\n"
    torrent_list += "• Reply to a torrent message with <code>/rename Better Name</code>"
    
    await sendMessage(torrent_list, context, parse_mode='HTML')


# List torrents command handler
list_torrents_handler = CommandHandler(BotCommands.ListTorrentsCommand, list_torrents,
                                       filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
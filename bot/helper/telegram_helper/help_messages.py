"""
Help messages for bot commands
"""

# Help messages for Mega.nz JDownloader commands
MEGA_JD_HELP = """
🔄 **Mega.nz JDownloader Commands**

📥 **/megajd** `<mega_link>` - Download Mega.nz files using JDownloader
   • Supports both file and folder links
   • Automatically uploads to Google Drive when complete
   • Example: `/megajd https://mega.nz/file/example123`

📊 **/megajdstatus** - Check JDownloader status and active downloads
   • Shows current download progress
   • Displays queue information
   • Example: `/megajdstatus`

⚙️ **Setup Required:**
1. Create `config.json` with your MyJDownloader credentials
2. Ensure JDownloader is running on your device
3. Have a MyJDownloader account at [my.jdownloader.org](https://my.jdownloader.org)

🔧 **Configuration:**
```json
{
  "jdownloader": {
    "email": "your_email@example.com",
    "password": "your_password",
    "device_name": "your_device_name"
  }
}
```

💡 **Features:**
• Automated Mega.nz link processing
• Progress monitoring
• Google Drive upload integration
• Error handling and retry logic
• Support for multiple concurrent downloads
"""

# General help message including new commands
BOT_HELP = """
🤖 **Mirror Bot Commands**

📥 **Download Commands:**
• `/mirror` `<link>` - Download and upload to Google Drive
• `/megajd` `<mega_link>` - Download Mega.nz files using JDownloader ⭐
• `/tarmirror` `<link>` - Download and upload as tar
• `/unzipmirror` `<link>` - Download, extract and upload

📊 **Status Commands:**
• `/status` - Show download status
• `/megajdstatus` - Show JDownloader status ⭐
• `/list` - List files in Google Drive

⚙️ **Control Commands:**
• `/cancel` `<gid>` - Cancel a download
• `/cancelall` - Cancel all downloads
• `/restart` - Restart the bot

🔐 **Authorization:**
• `/authorize` - Authorize a chat/user
• `/unauthorize` - Unauthorize a chat/user

📁 **Other Commands:**
• `/clone` `<drive_link>` - Clone Google Drive files
• `/watch` `<youtube_link>` - Download YouTube videos
• `/tgupload` - Upload Telegram files to Google Drive

⭐ **New Mega.nz JDownloader Integration**
Use `/megajd` for reliable Mega.nz downloads with JDownloader!
"""

# Command examples
COMMAND_EXAMPLES = """
📚 **Command Examples:**

**Mega.nz Downloads:**
```
/megajd https://mega.nz/file/example123
/megajd https://mega.nz/folder/folder123
/megajdstatus
```

**Regular Downloads:**
```
/mirror https://example.com/file.zip
/tarmirror https://example.com/folder.zip
/unzipmirror https://example.com/archive.zip
```

**YouTube Downloads:**
```
/watch https://youtube.com/watch?v=example
/tarwatch https://youtube.com/watch?v=example
```

**Google Drive:**
```
/clone https://drive.google.com/file/d/example/view
/list
```
"""
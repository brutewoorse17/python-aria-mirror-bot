# Bot Integration Guide: Mega.nz JDownloader

This guide explains how to integrate the Mega.nz JDownloader functionality with your existing Telegram Mirror Bot.

## 🚀 What's New

The bot now includes:
- **`/megajd`** command for Mega.nz downloads using JDownloader
- **`/megajdstatus`** command to check JDownloader status
- **`/megajdhelp`** command for detailed help
- **Enhanced `/help`** command with Mega.nz information
- **Updated `/start`** command introducing new features

## 📁 New Files Added

```
bot/
├── modules/
│   ├── mega_jdownloader.py      # Main Mega.nz JDownloader module
│   ├── help.py                  # Enhanced help system
│   └── start.py                 # Updated start command
├── helper/telegram_helper/
│   └── help_messages.py         # Help message templates
└── __init__.py                  # Updated with new commands

# Root level files
├── mega_jdownloader_api.py      # Core JDownloader API integration
├── config.json                  # JDownloader configuration
├── bot_config_mega_jd.json     # Bot-specific configuration
└── BOT_INTEGRATION_GUIDE.md    # This guide
```

## ⚙️ Setup Instructions

### 1. Install Dependencies

```bash
# Install required Python packages
pip3 install -r requirements-mega.txt

# Or install individually
pip3 install requests urllib3
```

### 2. Configure JDownloader

Create `config.json` in your bot's root directory:

```json
{
  "jdownloader": {
    "email": "your_email@example.com",
    "password": "your_password",
    "device_name": "your_device_name",
    "api_url": "https://api.jdownloader.org"
  }
}
```

**Important:**
- Use your MyJDownloader account credentials
- `device_name` is optional (leave empty for auto-detection)
- Never commit this file to version control

### 3. Alternative: Environment Variables

Instead of `config.json`, you can use environment variables:

```bash
export JDOWNLOADER_EMAIL="your_email@example.com"
export JDOWNLOADER_PASSWORD="your_password"
export JDOWNLOADER_DEVICE_NAME="your_device_name"
export JDOWNLOADER_API_URL="https://api.jdownloader.org"
```

### 4. Ensure JDownloader is Running

Make sure JDownloader is installed and running on your system:

```bash
# Check if JDownloader is running
ps aux | grep JDownloader

# Start JDownloader if needed
jdownloader
```

## 🔧 Bot Configuration

### Update Bot Commands

The bot automatically registers new commands:

```python
# New commands added to BotCommands
BotCommands.MegaJDownloaderCommand = 'megajd'
BotCommands.MegaJDownloaderStatusCommand = 'megajdstatus'
BotCommands.MegaJDownloaderHelpCommand = 'megajdhelp'
BotCommands.HelpCommand = 'help'
BotCommands.ExamplesCommand = 'examples'
```

### Handler Registration

New command handlers are automatically registered:

```python
# Mega.nz JDownloader handlers
mega_jdownloader_handler = CommandHandler(
    BotCommands.MegaJDownloaderCommand, 
    mega_jdownloader,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user
)

mega_jdownloader_status_handler = CommandHandler(
    BotCommands.MegaJDownloaderStatusCommand, 
    mega_jdownloader_status,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user
)
```

## 📱 Usage Examples

### Basic Mega.nz Downloads

```bash
# Download a single file
/megajd https://mega.nz/file/example123

# Download a folder
/megajd https://mega.nz/folder/folder123

# Check status
/megajdstatus
```

### Help Commands

```bash
# General help
/help

# Mega.nz specific help
/help megajd

# Command examples
/examples

# Start message
/start
```

## 🔄 How It Works

### 1. Command Processing

1. User sends `/megajd <mega_link>`
2. Bot validates the Mega.nz link
3. Creates a `MegaJDownloaderListener` instance
4. Initializes `MegaJDownloaderHelper` with configuration

### 2. Download Process

1. **Link Validation**: Checks if it's a valid Mega.nz URL
2. **JDownloader Integration**: Uses MyJDownloader API to add links
3. **Progress Monitoring**: Thread monitors download progress
4. **Completion Handling**: Automatically starts Google Drive upload
5. **Status Updates**: Provides real-time status updates

### 3. Upload Integration

1. **File Detection**: Automatically detects downloaded files
2. **Upload Status**: Creates upload status for tracking
3. **Google Drive Upload**: Integrates with existing drive tools
4. **Progress Tracking**: Shows upload progress in bot

## 🐛 Troubleshooting

### Common Issues

1. **"JDownloader configuration not found"**
   - Ensure `config.json` exists and has correct credentials
   - Check environment variables if using that method

2. **"Login failed"**
   - Verify MyJDownloader credentials
   - Ensure account is active and has devices connected

3. **"No devices found"**
   - Make sure JDownloader is running on at least one device
   - Check MyJDownloader dashboard for device status

4. **"Invalid Mega.nz link"**
   - Verify link format: `https://mega.nz/file/...` or `https://mega.nz/folder/...`
   - Ensure link is accessible

### Debug Mode

Enable verbose logging:

```bash
# Set logging level
export PYTHONPATH=.
python3 -u bot/__main__.py

# Check bot logs
tail -f log.txt
```

### Check JDownloader Status

```bash
# Check if JDownloader is running
ps aux | grep JDownloader

# Check JDownloader logs
tail -f ~/.jd/logs/jd.log

# Test API connection
python3 mega_jdownloader_api.py --email "..." --password "..." --help
```

## 🔒 Security Considerations

- **Never share credentials** - Keep `config.json` private
- **Use environment variables** for production deployments
- **Regular password updates** - Change MyJDownloader password periodically
- **Device management** - Remove unused devices from MyJDownloader

## 📊 Monitoring and Logging

### Bot Logs

The bot logs all Mega.nz JDownloader activities:

```python
LOGGER.info(f"Mega.nz JDownloader download started: {link}")
LOGGER.info(f"Added Mega.nz link to JDownloader: {link}")
LOGGER.error(f"Error adding download: {e}")
```

### Status Updates

Users can monitor progress with:

```bash
/megajdstatus    # Check JDownloader status
/status          # Check bot download status
```

## 🚀 Advanced Features

### Custom Download Folders

```python
# In the bot module
helper.add_download(link, f'{DOWNLOAD_DIR}{listener.uid}/custom_folder/')
```

### Concurrent Downloads

The system supports multiple concurrent Mega.nz downloads:

```python
# Multiple downloads
/megajd https://mega.nz/file/file1
/megajd https://mega.nz/file/file2
/megajd https://mega.nz/folder/folder1
```

### Error Recovery

- Automatic retry on failures
- Progress preservation
- Detailed error reporting

## 🔄 Integration Points

### Existing Bot Systems

The Mega.nz JDownloader integrates with:

1. **Authorization System**: Uses existing `CustomFilters`
2. **Status Management**: Integrates with `download_dict`
3. **Upload System**: Uses existing Google Drive tools
4. **Message System**: Uses existing message utilities
5. **Logging**: Uses existing bot logger

### File Structure

```
bot/
├── modules/mega_jdownloader.py  # Main integration
├── helper/telegram_helper/      # Bot utilities
│   ├── bot_commands.py         # Command definitions
│   ├── help_messages.py        # Help content
│   └── message_utils.py        # Message handling
└── __init__.py                 # Bot initialization
```

## 📈 Performance Considerations

- **Memory Usage**: Minimal memory footprint
- **API Calls**: Efficient MyJDownloader API usage
- **Concurrency**: Supports multiple simultaneous downloads
- **Monitoring**: Lightweight progress monitoring

## 🔮 Future Enhancements

Potential improvements:

1. **Batch Processing**: Process multiple links in one command
2. **Scheduled Downloads**: Schedule downloads for off-peak hours
3. **Download Limits**: Configurable download speed limits
4. **File Filtering**: Download specific file types only
5. **Progress Callbacks**: Real-time progress updates via bot

## 📞 Support

For issues or questions:

1. Check this integration guide
2. Review bot logs for error details
3. Verify JDownloader configuration
4. Test with simple Mega.nz links first

---

**Happy downloading with your enhanced Mirror Bot! 🚀**
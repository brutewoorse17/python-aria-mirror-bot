# MEGA.nz Download Support using JDownloader

This project now includes enhanced MEGA download support using JDownloader, providing better download management, resume capabilities, and improved reliability for MEGA.nz links.

## 🚀 Features

- **Enhanced MEGA Downloads**: Uses JDownloader for better MEGA link handling
- **Download Resume**: Automatically resumes interrupted downloads
- **Better Error Handling**: Improved error reporting and recovery
- **Web Interface**: Access JDownloader's web interface for manual management
- **API Integration**: Full integration with the existing bot system
- **Docker Support**: Easy deployment using Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose installed
- JDownloader account (free)
- MEGA.nz account (optional, for premium features)
- Telegram Bot Token
- Google Drive API credentials

## 🛠️ Installation

### 1. Quick Setup

```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd <repo-directory>

# Run the setup script
./setup_jdownloader.sh
```

### 2. Manual Setup

#### Step 1: Configure Environment
```bash
# Copy the configuration template
cp config_jdownloader.env config.env

# Edit the configuration file
nano config.env
```

#### Step 2: Fill Required Values
```bash
# JDownloader Settings
JDOWNLOADER_USERNAME=your_jdownloader_username
JDOWNLOADER_PASSWORD=your_jdownloader_password

# Bot Settings
BOT_TOKEN=your_telegram_bot_token
OWNER_ID=your_telegram_user_id
GDRIVE_FOLDER_ID=your_google_drive_folder_id

# Redis Settings
REDIS_PASSWORD=your_redis_password

# Telegram API Settings
TELEGRAM_API=your_telegram_api_id
TELEGRAM_HASH=your_telegram_api_hash
USER_SESSION_STRING=your_session_string

# Optional: MEGA Account (for premium features)
MEGA_USERNAME=your_mega_email
MEGA_PASSWORD=your_mega_password
```

#### Step 3: Start Services
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `JDOWNLOADER_HOST` | JDownloader API host | No | `http://localhost:5800` |
| `JDOWNLOADER_USERNAME` | JDownloader username | Yes | - |
| `JDOWNLOADER_PASSWORD` | JDownloader password | Yes | - |
| `JDOWNLOADER_DEVICE_ID` | JDownloader device ID | No | Auto-detected |
| `MEGA_USERNAME` | MEGA account email | No | Anonymous mode |
| `MEGA_PASSWORD` | MEGA account password | No | Anonymous mode |

### JDownloader Setup

1. **Create JDownloader Account**:
   - Visit [JDownloader.org](https://jdownloader.org)
   - Create a free account
   - Note your username and password

2. **Configure JDownloader**:
   - Access web interface at `http://localhost:5800`
   - Login with your JDownloader credentials
   - Configure download directory and other settings

## 📱 Usage

### Telegram Bot Commands

The bot automatically detects MEGA links and uses JDownloader for downloads:

```
/mirror https://mega.nz/file/example#key
```

### Supported MEGA Link Formats

- **File Links**: `https://mega.nz/file/ID#key`
- **Folder Links**: `https://mega.nz/folder/ID#key`
- **Legacy Links**: `https://mega.co.nz/file/ID#key`

### Download Process

1. User sends MEGA link to bot
2. Bot validates the link format
3. Bot adds download to JDownloader
4. JDownloader handles the download with MEGA credentials
5. Bot monitors progress and provides updates
6. Download completes and uploads to Google Drive

## 🐳 Docker Services

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   JDownloader   │    │      Redis      │
│                 │    │                 │    │                 │
│ - MEGA Support  │◄──►│ - Download Mgmt │    │ - Session Store │
│ - Google Drive  │    │ - Resume Support│    │ - Auth Cache    │
│ - Status Updates│    │ - Web Interface │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Service Details

- **Bot Service**: Main Telegram bot with MEGA support
- **JDownloader Service**: Download management and MEGA handling
- **Redis Service**: Session storage and authentication

## 📊 Monitoring

### Web Interfaces

- **JDownloader**: `http://localhost:5800`
- **Bot Logs**: `docker-compose logs -f bot`
- **Service Status**: `docker-compose ps`

### Log Files

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f jdownloader
docker-compose logs -f bot
docker-compose logs -f redis
```

## 🔍 Troubleshooting

### Common Issues

#### 1. JDownloader Connection Failed
```bash
# Check if JDownloader is running
docker-compose ps jdownloader

# Check JDownloader logs
docker-compose logs jdownloader

# Verify credentials in config.env
cat config.env | grep JDOWNLOADER
```

#### 2. MEGA Downloads Failing
```bash
# Check MEGA credentials
cat config.env | grep MEGA

# Verify JDownloader can access MEGA
# Check JDownloader web interface for error messages
```

#### 3. Bot Not Responding
```bash
# Check bot logs
docker-compose logs bot

# Verify bot token and owner ID
cat config.env | grep -E "(BOT_TOKEN|OWNER_ID)"
```

### Debug Mode

Enable debug logging by setting environment variables:

```bash
# Add to config.env
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

## 🔄 Updates

### Update Services
```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d

# Check for updates
docker-compose images
```

### Update Bot Code
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## 📚 API Reference

### JDownloader API Endpoints

The bot uses these JDownloader API endpoints:

- `GET /api/v2/devices` - List available devices
- `GET /api/v2/downloads/{device_id}/packages` - List downloads
- `POST /api/v2/downloads/{device_id}/packages` - Add new download
- `GET /api/v2/downloads/{device_id}/packages/{package_id}` - Get download status
- `POST /api/v2/downloads/{device_id}/packages/{package_id}/stop` - Stop download

### MEGA Link Parsing

The bot automatically detects and parses MEGA links:

```python
# Supported patterns
MEGA_PATTERNS = [
    r'https?://mega\.nz/(file|folder)/[a-zA-Z0-9_-]+(?:#[a-zA-Z0-9_-]+)?',
    r'https?://mega\.co\.nz/(file|folder)/[a-zA-Z0-9_-]+(?:#[a-zA-Z0-9_-]+)?',
    r'https?://www\.mega\.nz/(file|folder)/[a-zA-Z0-9_-]+(?:#[a-zA-Z0-9_-]+)?'
]
```

## 🤝 Contributing

### Development Setup

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd <repo-directory>
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-venv.txt
   ```

3. **Run Tests**:
   ```bash
   python -m pytest tests/
   ```

### Code Structure

```
bot/
├── helper/
│   └── mirror_utils/
│       ├── download_utils/
│       │   ├── jdownloader_download.py      # General JDownloader support
│       │   └── mega_jdownloader_download.py # MEGA-specific JDownloader
│       └── status_utils/
│           └── jdownloader_status.py        # JDownloader status handling
├── modules/
│   └── mirror.py                            # Main mirror command
└── __init__.py                              # Bot initialization
```

## 📄 License

This project is licensed under the same license as the original repository.

## 🙏 Acknowledgments

- **JDownloader Team**: For the excellent download manager
- **MEGA.nz**: For the cloud storage service
- **Original Bot Authors**: For the foundation of this project

## 📞 Support

### Getting Help

1. **Check Documentation**: This README and the main project README
2. **Review Logs**: Use `docker-compose logs` to check for errors
3. **Verify Configuration**: Ensure all required environment variables are set
4. **Check Service Status**: Use `docker-compose ps` to verify all services are running

### Reporting Issues

When reporting issues, please include:

- Docker and Docker Compose versions
- Complete error logs
- Configuration file (with sensitive data removed)
- Steps to reproduce the issue

---

**Happy Downloading! 🚀**
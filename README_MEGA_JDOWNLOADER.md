# Mega.nz Link Downloader using JDownloader

This project provides automated downloading of Mega.nz links using JDownloader with full API integration. It supports both local JDownloader instances and remote management through MyJDownloader.

## Features

- ✅ **Automated Mega.nz link processing** - No manual copying needed
- ✅ **JDownloader API integration** - Full remote control
- ✅ **Multiple link support** - Process multiple links at once
- ✅ **Progress monitoring** - Real-time download status
- ✅ **Cross-platform** - Works on Windows, macOS, and Linux
- ✅ **Configurable** - Custom download folders and settings
- ✅ **Error handling** - Robust error handling and retry logic

## Prerequisites

1. **JDownloader installed** on your system
2. **MyJDownloader account** (free at [my.jdownloader.org](https://my.jdownloader.org))
3. **Python 3.6+** installed
4. **Internet connection** for API communication

## Installation

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd mega-jdownloader
```

### 2. Install Python Dependencies

```bash
pip3 install requests
```

### 3. Configure Your Credentials

Edit `config.json` with your MyJDownloader credentials:

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

**Important**: 
- Use the email/password from your MyJDownloader account
- `device_name` is optional - leave empty for auto-detection
- Never commit your credentials to version control

### 4. Make Scripts Executable (Linux/macOS)

```bash
chmod +x download_mega.sh
chmod +x mega_jdownloader_api.py
```

## Usage

### Method 1: Shell Script (Recommended)

```bash
# Download a single file
./download_mega.sh "https://mega.nz/file/example123"

# Download multiple files
./download_mega.sh "https://mega.nz/file/file1" "https://mega.nz/file/file2"

# Download a folder
./download_mega.sh "https://mega.nz/folder/folder123"
```

### Method 2: Python Script Directly

```bash
# Basic usage
python3 mega_jdownloader_api.py \
  --email "your_email@example.com" \
  --password "your_password" \
  "https://mega.nz/file/example123"

# With custom download folder
python3 mega_jdownloader_api.py \
  --email "your_email@example.com" \
  --password "your_password" \
  --download-folder "/custom/path" \
  "https://mega.nz/file/example123"

# With device name and monitoring
python3 mega_jdownloader_api.py \
  --email "your_email@example.com" \
  --password "your_password" \
  --device-name "MyComputer" \
  --monitor \
  --monitor-interval 60 \
  "https://mega.nz/file/example123"
```

### Method 3: Python Module

```python
from mega_jdownloader_api import MegaJDownloaderAPI, JDownloaderConfig

# Configure
config = JDownloaderConfig(
    email="your_email@example.com",
    password="your_password"
)

# Initialize downloader
downloader = MegaJDownloaderAPI(config)

# Download links
links = [
    "https://mega.nz/file/example1",
    "https://mega.nz/folder/example2"
]

success = downloader.download_mega_links(links, "/downloads")
if success:
    print("Downloads started successfully!")
```

## Configuration Options

### JDownloader Settings

| Option | Description | Default |
|--------|-------------|---------|
| `email` | MyJDownloader account email | Required |
| `password` | MyJDownloader account password | Required |
| `device_name` | Specific JDownloader device | Auto-detected |
| `api_url` | MyJDownloader API endpoint | `https://api.jdownloader.org` |

### Download Settings

| Option | Description | Default |
|--------|-------------|---------|
| `default_folder` | Default download directory | `/downloads` |
| `auto_start` | Automatically start downloads | `true` |
| `monitor_interval` | Status check interval (seconds) | `30` |

### Mega.nz Settings

| Option | Description | Default |
|--------|-------------|---------|
| `max_concurrent` | Maximum concurrent downloads | `3` |
| `retry_attempts` | Download retry attempts | `3` |
| `timeout` | Download timeout (seconds) | `300` |

## Troubleshooting

### Common Issues

1. **"JDownloader not found"**
   - Ensure JDownloader is installed and in your PATH
   - Use `--jdownloader-path` to specify custom location

2. **"Login failed"**
   - Verify your MyJDownloader credentials
   - Check if your account is active
   - Ensure you have at least one device connected

3. **"No devices found"**
   - Make sure JDownloader is running on at least one device
   - Check your MyJDownloader dashboard

4. **"Invalid Mega.nz link"**
   - Verify the link format: `https://mega.nz/file/...` or `https://mega.nz/folder/...`
   - Ensure the link is accessible

### Debug Mode

Enable verbose logging:

```bash
export PYTHONPATH=.
python3 -u mega_jdownloader_api.py --email "..." --password "..." "mega_link"
```

### Check JDownloader Status

```bash
# Check if JDownloader is running
ps aux | grep JDownloader

# Check JDownloader logs
tail -f ~/.jd/logs/jd.log
```

## Security Considerations

- **Never share your credentials** - Keep `config.json` private
- **Use environment variables** for production deployments
- **Regular password updates** - Change MyJDownloader password periodically
- **Device management** - Remove unused devices from MyJDownloader

## Advanced Usage

### Custom Download Folders

```bash
# Per-link custom folders
python3 mega_jdownloader_api.py \
  --email "..." --password "..." \
  --download-folder "/movies" \
  "https://mega.nz/file/movie1" \
  --download-folder "/music" \
  "https://mega.nz/file/music1"
```

### Batch Processing

```bash
# Process links from file
cat mega_links.txt | xargs -I {} ./download_mega.sh "{}"

# Process all links in directory
find . -name "*.txt" -exec cat {} \; | grep "mega.nz" | xargs ./download_mega.sh
```

### Integration with Other Tools

```bash
# Download from clipboard (Linux)
xclip -o | ./download_mega.sh

# Download from clipboard (macOS)
pbpaste | ./download_mega.sh

# Download from clipboard (Windows)
powershell -command "Get-Clipboard" | ./download_mega.sh
```

## API Reference

### MegaJDownloaderAPI Class

```python
class MegaJDownloaderAPI:
    def __init__(self, config: JDownloaderConfig)
    def download_mega_links(self, links: List[str], download_folder: str = None) -> bool
    def monitor_progress(self, interval: int = 30)
    def _is_valid_mega_link(self, url: str) -> bool
```

### MyJDownloaderAPI Class

```python
class MyJDownloaderAPI:
    def __init__(self, config: JDownloaderConfig)
    def login(self) -> bool
    def add_links(self, links: List[str], download_folder: str = None) -> bool
    def get_download_status(self) -> Dict
    def start_downloads(self) -> bool
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check this README and inline code comments
- **Community**: JDownloader forums and community

## Changelog

### Version 1.0.0
- Initial release
- Basic Mega.nz link support
- JDownloader API integration
- Progress monitoring
- Cross-platform compatibility

---

**Happy downloading! 🚀**
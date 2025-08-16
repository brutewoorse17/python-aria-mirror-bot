#!/bin/bash

echo "=========================================="
echo "JDownloader Setup for MEGA Downloads"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p jdownloader_config
mkdir -p redis_data
mkdir -p downloads
mkdir -p credentials

# Check if config file exists
if [ ! -f "config.env" ]; then
    echo "📝 Creating config.env from template..."
    cp config_jdownloader.env config.env
    echo "⚠️  Please edit config.env with your actual values before starting the services."
    echo "   Required fields:"
    echo "   - JDOWNLOADER_USERNAME and JDOWNLOADER_PASSWORD"
    echo "   - MEGA_USERNAME and MEGA_PASSWORD (optional)"
    echo "   - BOT_TOKEN, OWNER_ID, GDRIVE_FOLDER_ID"
    echo "   - REDIS_PASSWORD"
    echo "   - TELEGRAM_API, TELEGRAM_HASH, USER_SESSION_STRING"
    echo ""
    echo "   After editing config.env, run this script again to start the services."
    exit 0
fi

# Load environment variables
echo "🔧 Loading configuration..."
source config.env

# Validate required environment variables
required_vars=("JDOWNLOADER_USERNAME" "JDOWNLOADER_PASSWORD" "BOT_TOKEN" "OWNER_ID" "GDRIVE_FOLDER_ID" "REDIS_PASSWORD")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_${var,,}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing or invalid configuration values:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please edit config.env with your actual values and run this script again."
    exit 1
fi

echo "✅ Configuration validation passed"

# Update docker-compose.yml with actual values
echo "🔧 Updating docker-compose.yml with your configuration..."
sed -i "s/your_jdownloader_username/$JDOWNLOADER_USERNAME/g" docker-compose.yml
sed -i "s/your_jdownloader_password/$JDOWNLOADER_PASSWORD/g" docker-compose.yml
sed -i "s/your_redis_password/$REDIS_PASSWORD/g" docker-compose.yml
sed -i "s/your_mega_email/${MEGA_USERNAME:-your_mega_email}/g" docker-compose.yml
sed -i "s/your_mega_password/${MEGA_PASSWORD:-your_mega_password}/g" docker-compose.yml
sed -i "s/your_telegram_bot_token/$BOT_TOKEN/g" docker-compose.yml
sed -i "s/your_telegram_user_id/$OWNER_ID/g" docker-compose.yml
sed -i "s/your_google_drive_folder_id/$GDRIVE_FOLDER_ID/g" docker-compose.yml
sed -i "s/your_telegram_api_id/${TELEGRAM_API:-your_telegram_api_id}/g" docker-compose.yml
sed -i "s/your_telegram_api_hash/${TELEGRAM_HASH:-your_telegram_api_hash}/g" docker-compose.yml
sed -i "s/your_session_string/${USER_SESSION_STRING:-your_session_string}/g" docker-compose.yml

echo "✅ docker-compose.yml updated"

# Start services
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "=========================================="
echo "Services started successfully!"
echo "=========================================="
echo ""
echo "🌐 JDownloader Web Interface: http://localhost:5800"
echo "🔌 JDownloader API: http://localhost:5700"
echo "📱 Telegram Bot: Check your bot for /start command"
echo ""
echo "📁 Download directory: ./downloads"
echo "⚙️  JDownloader config: ./jdownloader_config"
echo "🗄️  Redis data: ./redis_data"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart services: docker-compose restart"
echo "   - Update services: docker-compose pull && docker-compose up -d"
echo ""
echo "🔍 To check service status:"
echo "   docker-compose ps"
echo ""
echo "✅ Setup complete! Your MEGA downloads will now use JDownloader."
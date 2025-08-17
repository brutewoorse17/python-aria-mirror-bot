from http.client import NotConnected
import logging
import os
import threading
import time
from bot.helper.mirror_utils.download_utils.aioaria2_adapter import AioAria2API
from telegram.ext import Application
from dotenv import load_dotenv
import socket
# Mega client will be imported lazily in mega_download to avoid event loop issues
import subprocess
import redis

socket.setdefaulttimeout(600)

botStartTime = time.time()
if os.path.exists('log.txt'):
    with open('log.txt', 'r+') as f:
        f.truncate(0)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('log.txt'), logging.StreamHandler()],
                    level=logging.INFO)

load_dotenv('config.env')

Interval = []


def getConfig(name: str):
    return os.environ[name]


LOGGER = logging.getLogger(__name__)

try:
    if bool(getConfig('_____REMOVE_THIS_LINE_____')):
        logging.error('The README.md file there to be read! Exiting now!')
        exit()
except KeyError:
    pass

aria2 = AioAria2API(
	"http://localhost:6800/jsonrpc",
	token=""
)

DOWNLOAD_DIR = None
BOT_TOKEN = None

# Shared state
application = None
bot = None

download_dict_lock = threading.Lock()
status_reply_dict_lock = threading.Lock()
# Key: update.effective_chat.id
# Value: telegram.Message
status_reply_dict = {}
# Key: update.message.message_id
# Value: An object of Status
download_dict = {}
# Stores list of users and chats the bot is authorized to use in
redis_client = None
AUTHORIZED_CHATS = set()
WAITING_FOR_TOKEN_PICKLE = False

redis_authorised_chats_key = 'bots:authorized_chats'

def redis_init():
    global redis_client
    try:
        host = getConfig('REDIS_HOST')
        port = int(getConfig('REDIS_PORT'))
        password = getConfig('REDIS_PASSWORD')
        if not host:
            LOGGER.warning('REDIS_HOST not set; skipping Redis initialization')
            return
        redis_client = redis.Redis(host=host, port=port, password=password)
        ids = redis_client.smembers(redis_authorised_chats_key)
        for id in ids:
            AUTHORIZED_CHATS.add(int(id))
        LOGGER.info('Redis initialized; authorized chats loaded')
    except Exception as e:
        LOGGER.error(f'Redis init failed: {e}. Continuing without Redis persistence')
        redis_client = None

redis_thread = threading.Thread(target=redis_init)
redis_thread.start()
try:
    BOT_TOKEN = getConfig('BOT_TOKEN')
    parent_id = getConfig('GDRIVE_FOLDER_ID')
    DOWNLOAD_DIR = getConfig('DOWNLOAD_DIR')
    if DOWNLOAD_DIR[-1] != '/' or DOWNLOAD_DIR[-1] != '\\':
        DOWNLOAD_DIR = DOWNLOAD_DIR + '/'
    DOWNLOAD_STATUS_UPDATE_INTERVAL = int(getConfig('DOWNLOAD_STATUS_UPDATE_INTERVAL'))
    OWNER_ID = int(getConfig('OWNER_ID'))
    AUTO_DELETE_MESSAGE_DURATION = int(getConfig('AUTO_DELETE_MESSAGE_DURATION'))
    USER_SESSION_STRING = getConfig('USER_SESSION_STRING')
    TELEGRAM_API = getConfig('TELEGRAM_API')
    TELEGRAM_HASH = getConfig('TELEGRAM_HASH')
except KeyError as e:
    LOGGER.error("One or more env variables missing! Exiting now")
    exit(1)

try:
    MEGA_KEY = getConfig('MEGA_KEY')
except KeyError:
    MEGA_KEY = None
    LOGGER.info('MEGA API KEY NOT AVAILABLE')
# Defer starting megasdkrest until first Mega download to avoid event loop issues
MEGA_USERNAME = None
MEGA_PASSWORD = None
if MEGA_KEY is not None:
    # Start megasdkrest binary
    subprocess.Popen(["megasdkrest", "--apikey", MEGA_KEY])
    time.sleep(3)  # Wait for the mega server to start listening
    # mega_client = MegaSdkRestClient('http://localhost:6090') # This line was commented out in the original file
    try:
        MEGA_USERNAME = getConfig('MEGA_USERNAME')
        MEGA_PASSWORD = getConfig('MEGA_PASSWORD')
        if len(MEGA_USERNAME) > 0 and len(MEGA_PASSWORD) > 0:
            try:
                # mega_client.login(MEGA_USERNAME, MEGA_PASSWORD) # This line was commented out in the original file
                pass # Placeholder for actual mega_client.login call if mega_client is defined
            except Exception as e: # Changed from mega_err.MegaSdkRestClientException to Exception
                logging.error(e)
                exit(0)
        else:
            LOGGER.info("Mega API KEY provided but credentials not provided. Starting mega in anonymous mode!")
            MEGA_USERNAME = None
            MEGA_PASSWORD = None
    except KeyError:
        LOGGER.info("Mega API KEY provided but credentials not provided. Starting mega in anonymous mode!")
        MEGA_USERNAME = None
        MEGA_PASSWORD = None
else:
    MEGA_USERNAME = None
    MEGA_PASSWORD = None
try:
    INDEX_URL = getConfig('INDEX_URL')
    if len(INDEX_URL) == 0:
        INDEX_URL = None
except KeyError:
    INDEX_URL = None
try:
    UPLOAD_AS_VIDEO = getConfig('UPLOAD_AS_VIDEO')
    if isinstance(UPLOAD_AS_VIDEO, str):
        UPLOAD_AS_VIDEO = True if UPLOAD_AS_VIDEO.lower() == 'true' else False
except KeyError:
    UPLOAD_AS_VIDEO = False
try:
    VIDEO_THUMB_PATH = getConfig('VIDEO_THUMB_PATH')
    if len(VIDEO_THUMB_PATH) == 0:
        VIDEO_THUMB_PATH = None
except KeyError:
    VIDEO_THUMB_PATH = None
try:
    USE_CUSTOM_THUMB = getConfig('USE_CUSTOM_THUMB')
    if isinstance(USE_CUSTOM_THUMB, str):
        USE_CUSTOM_THUMB = True if USE_CUSTOM_THUMB.lower() == 'true' else False
except KeyError:
    USE_CUSTOM_THUMB = False
try:
    TG_PART_SIZE_MB = int(getConfig('TG_PART_SIZE_MB'))
    if TG_PART_SIZE_MB <= 0:
        TG_PART_SIZE_MB = 1950
except KeyError:
    TG_PART_SIZE_MB = 1950
try:
    IS_TEAM_DRIVE = getConfig('IS_TEAM_DRIVE')
    if IS_TEAM_DRIVE.lower() == 'true':
        IS_TEAM_DRIVE = True
    else:
        IS_TEAM_DRIVE = False
except KeyError:
    IS_TEAM_DRIVE = False

try:
    USE_SERVICE_ACCOUNTS = getConfig('USE_SERVICE_ACCOUNTS')
    if USE_SERVICE_ACCOUNTS.lower() == 'true':
        USE_SERVICE_ACCOUNTS = True
    else:
        USE_SERVICE_ACCOUNTS = False
except KeyError:
    USE_SERVICE_ACCOUNTS = False

# Build Application and bot
application = Application.builder().token(BOT_TOKEN).build()
bot = application.bot

redis_thread.join()
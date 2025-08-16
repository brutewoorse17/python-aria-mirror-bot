from bot.helper.telegram_helper.message_utils import sendMessage
from bot import AUTHORIZED_CHATS, application
from telegram.ext import CommandHandler
from bot.helper.telegram_helper.filters import CustomFilters
from telegram import Update
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot import redis_client, redis_authorised_chats_key

async def authorize(update,context):
    reply_message = update.message.reply_to_message
    msg = ''
    if reply_message is None:
        # Trying to authorize a chat
        chat_id = update.effective_chat.id
        if chat_id not in AUTHORIZED_CHATS:
            redis_client.sadd(redis_authorised_chats_key, chat_id)
            AUTHORIZED_CHATS.add(chat_id)
            msg = 'Chat authorized'
        else:
            msg = 'Already authorized chat'
    else:
        # Trying to authorize someone in specific
        user_id = reply_message.from_user.id
        if user_id not in AUTHORIZED_CHATS:
            redis_client.sadd(redis_authorised_chats_key, user_id)
            AUTHORIZED_CHATS.add(user_id)
            msg = 'Person Authorized to use the bot!'
        else:
            msg = 'Person already authorized'
    await sendMessage(msg, context)


async def unauthorize(update,context):
    reply_message = update.message.reply_to_message
    if reply_message is None:
        # Trying to unauthorize a chat
        chat_id = update.effective_chat.id
        if chat_id in AUTHORIZED_CHATS:
            AUTHORIZED_CHATS.remove(chat_id)
            redis_client.srem(redis_authorised_chats_key, chat_id)
            msg = 'Chat unauthorized'
        else:
            msg = 'Already unauthorized chat'
    else:
        # Trying to authorize someone in specific
        user_id = reply_message.from_user.id
        if user_id in AUTHORIZED_CHATS:
            AUTHORIZED_CHATS.remove(user_id)
            redis_client.srem(redis_authorised_chats_key, user_id)
            msg = 'Person unauthorized to use the bot!'
        else:
            msg = 'Person already unauthorized!'
        
    await sendMessage(msg, context)


authorize_handler = CommandHandler(command=BotCommands.AuthorizeCommand, callback=authorize,
                                   filters=CustomFilters.owner_filter & CustomFilters.authorized_chat)
unauthorize_handler = CommandHandler(command=BotCommands.UnAuthorizeCommand, callback=unauthorize,
                                     filters=CustomFilters.owner_filter & CustomFilters.authorized_chat)
application.add_handler(authorize_handler)
application.add_handler(unauthorize_handler)


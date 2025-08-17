from telegram import Message
from telegram import Update
import time
from bot import AUTO_DELETE_MESSAGE_DURATION, LOGGER, bot, \
    status_reply_dict, status_reply_dict_lock
from bot.helper.ext_utils.bot_utils import get_readable_message
from telegram.error import TimedOut, BadRequest
from bot import bot
from bot import application


async def sendMessage(text: str, context, update: Update = None):
    try:
        if not text:
            text = " "
        if update is None:
            chat_id = getattr(getattr(context, 'chat_data', None), 'id', None) or getattr(getattr(context, 'chat', None), 'id', None)
            message_id = None
        else:
            chat_id = update.effective_chat.id
            message_id = update.effective_message.message_id
        return await context.bot.send_message(chat_id,
                            reply_to_message_id=message_id,
                            text=text, parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))


async def editMessage(text: str, message: Message, context):
    try:
        await context.bot.edit_message_text(text=text, message_id=message.message_id,
                              chat_id=message.chat.id,
                              parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))


async def deleteMessage(context, message: Message):
    try:
        await context.bot.delete_message(chat_id=message.chat.id,
                           message_id=message.message_id)
    except Exception as e:
        LOGGER.error(str(e))


async def sendLogFile(context, update: Update = None):
    with open('log.txt', 'rb') as f:
        if update is not None:
            await context.bot.send_document(document=f, filename=f.name,
                              reply_to_message_id=update.effective_message.message_id,
                              chat_id=update.effective_chat.id)
        else:
            await application.bot.send_document(document=f, filename=f.name,
                              chat_id=update.effective_chat.id)


async def _async_send_message(chat_id, reply_to_message_id, text, parse_mode='HTMl'):
    try:
        await application.bot.send_message(chat_id, reply_to_message_id=reply_to_message_id, text=text, parse_mode=parse_mode)
    except Exception as e:
        LOGGER.error(str(e))


def send_message_async(chat_id, reply_to_message_id, text, parse_mode='HTMl'):
    application.create_task(_async_send_message(chat_id, reply_to_message_id, text, parse_mode))


def auto_delete_message(cmd_message: Message, bot_message: Message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        time.sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            if cmd_message:
                application.create_task(application.bot.delete_message(chat_id=cmd_message.chat.id, message_id=cmd_message.message_id))
            if bot_message:
                application.create_task(application.bot.delete_message(chat_id=bot_message.chat.id, message_id=bot_message.message_id))
        except Exception as e:
            LOGGER.error(str(e))


def delete_all_messages():
    with status_reply_dict_lock:
        for message in list(status_reply_dict.values()):
            try:
                if not message or not getattr(message, 'chat', None):
                    continue
                application.create_task(application.bot.delete_message(chat_id=message.chat.id,
                                   message_id=message.message_id))
                del status_reply_dict[message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))


def update_all_messages():
    msg = get_readable_message()
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id].text:
                try:
                    bot.edit_message_text(text=msg, message_id=status_reply_dict[chat_id].message_id,
                                          chat_id=status_reply_dict[chat_id].chat.id,
                                          parse_mode='HTMl')
                except Exception as e:
                    LOGGER.error(str(e))
                status_reply_dict[chat_id].text = msg


async def sendStatusMessage(msg, context):
    progress = get_readable_message()
    with status_reply_dict_lock:
        if msg.message.chat.id in list(status_reply_dict.keys()):
            try:
                message = status_reply_dict[msg.message.chat.id]
                await deleteMessage(context, message)
                del status_reply_dict[msg.message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))
                del status_reply_dict[msg.message.chat.id]
        message = await sendMessage(progress, context, update=msg)
        status_reply_dict[msg.message.chat.id] = message

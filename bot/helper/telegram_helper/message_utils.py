from telegram.message import Message
from telegram.update import Update
import time
from bot import AUTO_DELETE_MESSAGE_DURATION, LOGGER, bot, \
    status_reply_dict, status_reply_dict_lock
from bot.helper.ext_utils.bot_utils import get_readable_message
from telegram.error import TimedOut, BadRequest
from bot import bot


async def sendMessage(text: str, context):
    try:
        return await context.bot.send_message(context._update.effective_chat.id,
                            reply_to_message_id=context._update.effective_message.message_id,
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


async def sendLogFile(context):
    with open('log.txt', 'rb') as f:
        await context.bot.send_document(document=f, filename=f.name,
                          reply_to_message_id=context._update.effective_message.message_id,
                          chat_id=context._update.effective_chat.id)


def auto_delete_message(bot, cmd_message: Message, bot_message: Message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        time.sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            # Skip if None is passed meaning we don't want to delete bot xor cmd message
            deleteMessage(bot, cmd_message)
            deleteMessage(bot, bot_message)
        except AttributeError:
            pass


def delete_all_messages():
    with status_reply_dict_lock:
        for message in list(status_reply_dict.values()):
            try:
                # In async flow we cannot await here; relying on older sync bot for cleanup
                bot.delete_message(chat_id=message.chat.id,
                                   message_id=message.message_id)
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
        message = await sendMessage(progress, context)
        status_reply_dict[msg.message.chat.id] = message

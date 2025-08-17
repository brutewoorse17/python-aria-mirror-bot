from telegram import Message
from telegram import Update
import time
from bot import AUTO_DELETE_MESSAGE_DURATION, LOGGER, bot, \
    status_reply_dict, status_reply_dict_lock, application
from bot.helper.ext_utils.bot_utils import get_readable_message
from telegram.error import TimedOut, BadRequest
import asyncio


async def sendMessage(text: str, context, update: Update = None):
    try:
        if not text or text.strip() == "":
            text = " "  # Ensure we always have at least a space
        if update is None:
            chat_id = getattr(getattr(context, 'chat_data', None), 'id', None) or getattr(getattr(context, 'chat', None), 'id', None)
            message_id = None
        else:
            chat_id = update.effective_chat.id
            message_id = update.effective_message.message_id
        
        # Validate chat_id before sending
        if not chat_id:
            LOGGER.error("Invalid chat_id in sendMessage")
            return None
            
        return await context.bot.send_message(chat_id,
                            reply_to_message_id=message_id,
                            text=text, parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(f"Error in sendMessage: {str(e)}")
        return None


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


def send_message_async(chat_id, reply_to_message_id, text, parse_mode='HTMl'):
    # Create a coroutine for sending the message
    async def send_message():
        try:
            await application.bot.send_message(chat_id, reply_to_message_id=reply_to_message_id, text=text, parse_mode=parse_mode)
        except Exception as e:
            LOGGER.error(f"Error sending message: {e}")
    
    # Schedule the coroutine
    _schedule_coroutine(send_message())


def auto_delete_message(cmd_message: Message, bot_message: Message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        time.sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            # Create coroutines for deleting messages
            async def delete_cmd_message():
                try:
                    if cmd_message and hasattr(cmd_message, 'chat') and hasattr(cmd_message, 'message_id'):
                        await application.bot.delete_message(chat_id=cmd_message.chat.id, message_id=cmd_message.message_id)
                    else:
                        LOGGER.warning("Invalid cmd_message object in auto_delete_message")
                except Exception as e:
                    LOGGER.error(f"Error deleting cmd message: {e}")
            
            async def delete_bot_message():
                try:
                    if bot_message and hasattr(bot_message, 'chat') and hasattr(bot_message, 'message_id'):
                        await application.bot.delete_message(chat_id=bot_message.chat.id, message_id=bot_message.message_id)
                    else:
                        LOGGER.warning("Invalid bot_message object in auto_delete_message")
                except Exception as e:
                    LOGGER.error(f"Error deleting bot message: {e}")
            
            # Schedule the coroutines
            if cmd_message:
                _schedule_coroutine(delete_cmd_message())
            if bot_message:
                _schedule_coroutine(delete_bot_message())
        except Exception as e:
            LOGGER.error(str(e))


def delete_all_messages():
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            try:
                if not status_reply_dict[chat_id]:
                    continue
                
                try:
                    message_obj, _ = status_reply_dict[chat_id]
                    # Validate message_obj before using it
                    if not message_obj or not hasattr(message_obj, 'chat') or not hasattr(message_obj, 'message_id'):
                        LOGGER.warning(f"Invalid message object for chat {chat_id}, removing from status_reply_dict")
                        del status_reply_dict[chat_id]
                        continue
                    
                    # Create a coroutine for deleting the message
                    async def delete_message():
                        try:
                            await application.bot.delete_message(chat_id=message_obj.chat.id, message_id=message_obj.message_id)
                        except Exception as e:
                            LOGGER.error(f"Error deleting message: {e}")
                    
                    # Schedule the coroutine
                    _schedule_coroutine(delete_message())
                    
                except Exception as e:
                    LOGGER.error(f"Error processing message object for chat {chat_id}: {str(e)}")
                
                del status_reply_dict[chat_id]
            except Exception as e:
                LOGGER.error(f"Error in delete_all_messages for chat {chat_id}: {str(e)}")
                # Remove invalid entries
                del status_reply_dict[chat_id]


def _schedule_coroutine(coro):
    """Helper function to schedule a coroutine in the appropriate event loop"""
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're in an event loop, create a task
        asyncio.create_task(coro)
    except RuntimeError:
        # No event loop running, try to get the application's loop
        try:
            if hasattr(application, '_loop') and application._loop and application._loop.is_running():
                asyncio.run_coroutine_threadsafe(coro, application._loop)
            else:
                # Last resort: try to create a new event loop
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(coro)
                    loop.close()
                except Exception as e:
                    LOGGER.error(f"Could not schedule coroutine: {e}")
        except Exception as e:
            LOGGER.error(f"Could not access application loop: {e}")

def update_all_messages():
    msg = get_readable_message()
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id]:
                try:
                    message_obj, stored_text = status_reply_dict[chat_id]
                    # Validate message_obj before using it
                    if not message_obj or not hasattr(message_obj, 'chat') or not hasattr(message_obj, 'message_id'):
                        LOGGER.warning(f"Invalid message object for chat {chat_id}, removing from status_reply_dict")
                        del status_reply_dict[chat_id]
                        continue
                    
                    if msg != stored_text:
                        try:
                            # Create a coroutine for editing the message
                            async def edit_message():
                                try:
                                    await bot.edit_message_text(
                                        text=msg, 
                                        message_id=message_obj.message_id,
                                        chat_id=message_obj.chat.id,
                                        parse_mode='HTMl'
                                    )
                                except Exception as e:
                                    LOGGER.error(f"Error editing message: {e}")
                            
                            # Schedule the coroutine
                            _schedule_coroutine(edit_message())
                            
                            # Update the stored text
                            status_reply_dict[chat_id] = (message_obj, msg)
                        except Exception as e:
                            LOGGER.error(f"Error in update_all_messages for chat {chat_id}: {str(e)}")
                except Exception as e:
                    LOGGER.error(f"Error processing status_reply_dict entry for chat {chat_id}: {str(e)}")
                    # Remove invalid entries
                    del status_reply_dict[chat_id]


async def sendStatusMessage(msg, context):
    progress = get_readable_message()
    with status_reply_dict_lock:
        if msg.message.chat.id in list(status_reply_dict.keys()):
            try:
                message_obj, _ = status_reply_dict[msg.message.chat.id]
                if message_obj:  # Only delete if message_obj is not None
                    await deleteMessage(context, message_obj)
                del status_reply_dict[msg.message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))
                del status_reply_dict[msg.message.chat.id]
        
        message = await sendMessage(progress, context, update=msg)
        # Only store in status_reply_dict if message was sent successfully
        if message is not None:
            status_reply_dict[msg.message.chat.id] = (message, progress)
        else:
            LOGGER.error(f"Failed to send status message to chat {msg.message.chat.id}")

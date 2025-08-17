from telegram.ext import filters
from telegram import Message, Update
from bot import AUTHORIZED_CHATS, OWNER_ID, download_dict, download_dict_lock


class CustomFilters:
    # Simple functional filters compatible with PTB v21
    owner_filter = filters.User(user_id=OWNER_ID)

    class _AuthorizedUserFilter(filters.UpdateFilter):
        def filter(self, update: Update) -> bool:
            message = update.effective_message
            if not message or not message.from_user:
                return False
            user_id = message.from_user.id
            return bool(user_id in AUTHORIZED_CHATS or user_id == OWNER_ID)

    authorized_user = filters.UpdateType.MESSAGE & _AuthorizedUserFilter()

    class _AuthorizedChatFilter(filters.UpdateFilter):
        def filter(self, update: Update) -> bool:
            chat = update.effective_chat
            return bool(chat and chat.id in AUTHORIZED_CHATS)

    authorized_chat = filters.UpdateType.MESSAGE & _AuthorizedChatFilter()

    class _MirrorOwnerFilter(filters.UpdateFilter):
        def filter(self, update: Update) -> bool:
            message: Message = update.effective_message
            if not message or not message.from_user:
                return False
            user_id = message.from_user.id
            if user_id == OWNER_ID:
                return True
            args = str(message.text or '').split(' ')
            if len(args) > 1:
                # Cancelling by gid
                with download_dict_lock:
                    for message_id, status in download_dict.items():
                        if status.gid() == args[1] and status.message.from_user.id == user_id:
                            return True
                    else:
                        return False
            # Cancelling by replying to original mirror message
            reply = message.reply_to_message
            if not reply or not reply.from_user:
                return False
            reply_user = reply.from_user.id
            return bool(reply_user == user_id)

    mirror_owner_filter = filters.UpdateType.MESSAGE & _MirrorOwnerFilter()

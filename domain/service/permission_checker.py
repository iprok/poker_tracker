from config import CHANNEL_ID
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus


class PermissionChecker:
    @staticmethod
    async def check_is_group_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id

            chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
            if chat_member.status in [
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            ]:
                return True

            return False
        except:
            return False

    @staticmethod
    async def check_is_chat_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type == "private":
            return True
        return False

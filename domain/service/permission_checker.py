from config import CHANNEL_ID
from telegram import Update
from telegram.ext import ContextTypes


class PermissionChecker:
    @staticmethod
    async def check_is_group_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_user.id
            chat_members = await context.bot.get_chat_member(CHANNEL_ID, user_id)

            return True
        except:
            return False

    @staticmethod
    async def check_is_chat_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type == "private":
            return True
        return False

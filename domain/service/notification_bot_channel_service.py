from telegram import Update


class NotificationBotChannelService:
    async def reply(self, update: Update, message: str) -> None:
        """Replies to the user who sent the command."""
        if update.message:
            await update.message.reply_text(message, parse_mode="HTML")

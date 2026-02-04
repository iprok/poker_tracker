from telegram import Bot


class NotificationPublicChannelService:
    def __init__(self, channel_id: int | str):
        self._channel_id = channel_id

    async def notify(self, bot: Bot, message: str) -> None:
        """Sends a notification to the configured channel."""
        await bot.send_message(
            chat_id=self._channel_id, text=message, parse_mode="HTML"
        )

from telegram import Update
from config import CHANNEL_ID


# Декоратор для ограничения команд только указанным каналом
def restrict_to_channel(func):
    async def wrapper(update: Update, context):
        if update.effective_chat.id != CHANNEL_ID:
            await update.message.reply_text(
                "Команды обрабатываются только в указанном канале."
            )
            return
        return await func(update, context)

    return wrapper

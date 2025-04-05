from telegram import Update
from config import CHANNEL_ID, BOT_ID


# Декоратор для ограничения команд только указанным каналом
def restrict_to_channel(func):
    async def wrapper(update: Update, context):
        if update.effective_chat.id != CHANNEL_ID:
            await update.message.reply_text(
                "Эта команда обрабатывается только в общем канале."
            )
            return
        return await func(update, context)

    return wrapper


# Декоратор для ограничения команд только указанным каналом
def restrict_to_bot(func):
    async def wrapper(update: Update, context):
        if update.effective_chat.id != BOT_ID:
            await update.message.reply_text(
                "Эта команда обрабатывается только в канале бота."
            )
            return
        return await func(update, context)

    return wrapper


# Декоратор для ограничения команд только указанным каналом или самим ботом
def restrict_to_all(func):
    async def wrapper(update: Update, context):
        aviableChannels = [BOT_ID, CHANNEL_ID]

        try:
            indexOfCurrentChannel = aviableChannels.index(update.effective_chat.id)

            return await func(update, context)
        except:
            await update.message.reply_text(
                "Эта команда может обрабатывать только в общем канале или в канале бота."
            )
            return

    return wrapper

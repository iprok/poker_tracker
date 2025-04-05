from telegram import Update
from config import CHANNEL_ID, BOT_ID


# Декоратор для ограничения команд только пользователями в канале
def restrict_to_members(func):
    async def wrapper(update: Update, context):

        try:
            user_id = update.effective_user.id
            chat_members = await context.bot.get_chat_member(CHANNEL_ID, user_id)

            return await func(update, context)
        except:
            await update.message.reply_text(
                "Эта команда обрабатывается только в канале бота."
            )
            return

    return wrapper


# Декоратор для ограничения команд только пользователями в канале + приватный чат с ботом
def restrict_to_members_and_private(func):
    async def wrapper(update: Update, context):

        try:
            user_id = update.effective_user.id
            chat_members = await context.bot.get_chat_member(CHANNEL_ID, user_id)

            if update.effective_chat.type == "private":
                return await func(update, context)

            raise Exception("Only for Private usage")
        except:
            await update.message.reply_text(
                "Эта команда обрабатывается только в канале бота."
            )
            return

    return wrapper

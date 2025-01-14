from telegram import Update
from config import CHANNEL_ID

# Декоратор для ограничения команд только указанным каналом
def restrict_to_channel(func):
    async def wrapper(update: Update, context):
        if update.effective_chat.id != CHANNEL_ID:
            await update.message.reply_text("Команды обрабатываются только в указанном канале.")
            return
        return await func(update, context)
    return wrapper

# Декоратор для ограничения команд только администраторам канала
def restrict_to_admins(func):
    async def wrapper(update: Update, context):
        chat_id = CHANNEL_ID
        user_id = update.effective_user.id

        # Получаем список администраторов канала
        chat_administrators = await context.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in chat_administrators]

        if user_id not in admin_ids:
            await update.message.reply_text("Эта команда доступна только администраторам канала.")
            return

        return await func(update, context)
    return wrapper

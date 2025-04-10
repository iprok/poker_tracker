from telegram import Update
from domain.service.permission_checker import PermissionChecker


# Декоратор для ограничения команд только пользователями в канале
def restrict_to_members(func):
    async def wrapper(update: Update, context):
        if await PermissionChecker.check_is_group_member(update, context):
            await func(update, context)
            return

        if update.message:
            await update.message.reply_text(
                "Эта команда обрабатывается только участниками группы."
            )
        return

    return wrapper


# Декоратор для ограничения команд только пользователями в канале + приватный чат с ботом
def restrict_to_members_and_private(func):
    async def wrapper(update: Update, context):
        if await PermissionChecker.check_is_group_member(
            update, context
        ) and await PermissionChecker.check_is_chat_private(update, context):
            await func(update, context)
            return

        if update.message:
            await update.message.reply_text(
                "Эта команда обрабатывается только в канале бота или участниками группы."
            )
        return

    return wrapper

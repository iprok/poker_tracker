#!/usr/bin/env python3

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from commands.game_management import GameManagement
from commands.player_actions import PlayerActions
from config import BOT_TOKEN


def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация команды для показа меню
    application.add_handler(CommandHandler("menu", PlayerActions.show_menu))
    application.add_handler(CommandHandler("close_menu", PlayerActions.close_menu))

    # Обработчик кнопки "Начать выход"
    application.add_handler(
        MessageHandler(
            filters.Regex(r".*\/startexit.*"), PlayerActions.handle_quit_button
        )
    )

    # Обработчик команды /quit
    application.add_handler(
        MessageHandler(filters.Regex(r".*\/quit.*"), PlayerActions.handle_quit_command)
    )

    # Обработчик подтверждения
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^(Да, вывести \d+|Нет, отменить)$"),
            PlayerActions.handle_confirmation,
        )
    )

    # Регистрация других команд
    application.add_handler(CommandHandler("startgame", GameManagement.start_game))
    application.add_handler(CommandHandler("endgame", GameManagement.end_game))
    application.add_handler(CommandHandler("buyin", PlayerActions.buyin))
    application.add_handler(CommandHandler("summary", PlayerActions.summary))
    application.add_handler(CommandHandler("summarygames", PlayerActions.summarygames))
    application.add_handler(CommandHandler("log", PlayerActions.log))
    application.add_handler(CommandHandler("help", PlayerActions.help))

    # Показываем меню при старте бота
    async def post_init(application):
        await application.bot.set_my_commands(
            [
                ("menu", "Показать меню команд"),
            ]
        )

    application.post_init = post_init

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    run_bot()

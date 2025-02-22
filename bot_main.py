#!/usr/bin/env python3

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from commands.game_management import GameManagement
from commands.player_actions import PlayerActions
from config import BOT_TOKEN

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация команд управления игрой
    application.add_handler(CommandHandler("startgame", GameManagement.start_game))
    application.add_handler(CommandHandler("endgame", GameManagement.end_game))

    # Регистрация обработчиков для русскоязычных текстовых команд
    application.add_handler(MessageHandler(filters.Regex(r"^/?закуп$"), PlayerActions.buyin))  # Только "закуп"
    application.add_handler(MessageHandler(filters.Regex(r"^/?выход"), PlayerActions.quit_with_args))

    # Регистрация команд действий игроков
    application.add_handler(CommandHandler("buyin", PlayerActions.buyin))
    application.add_handler(CommandHandler("quit", PlayerActions.quit))
    application.add_handler(CommandHandler("summary", PlayerActions.summary))
    application.add_handler(CommandHandler("summarygames", PlayerActions.summarygames))
    application.add_handler(CommandHandler("log", PlayerActions.log))
    application.add_handler(CommandHandler("help", PlayerActions.help))

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    run_bot()

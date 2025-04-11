import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import BotCommandScopeChat, BotCommandScopeAllPrivateChats
from commands.game_management import GameManagement
from commands.player_actions import PlayerActions
from config import BOT_TOKEN, CHANNEL_ID


async def post_init(application: Application) -> None:
    """Настройка команд после запуска бота."""
    try:
        await application.bot.set_my_commands(
            commands=[("menu", "Показать меню команд")],
            scope=BotCommandScopeChat(chat_id=CHANNEL_ID),
        )
    except Exception:
        await application.bot.delete_my_commands()

    await application.bot.set_my_commands(
        commands=[
            ("buyin", "Закуп"),
            ("quitgame", "Выйти"),
            ("menu", "Управление игрой"),
            ("mystats", "Ваша статистика"),
        ],
        scope=BotCommandScopeAllPrivateChats(),
    )


def build_application() -> Application:
    """Создаёт и настраивает экземпляр Telegram Application."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("menu", PlayerActions.show_menu))
    application.add_handler(CommandHandler("close_menu", PlayerActions.close_menu))
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^\s*/quitgame\s*"), PlayerActions.handle_quit_button
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^\s*/endgame\s*"), GameManagement.handle_endgame_command
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^\s*/quit(\s(0|\d{4,5}))?$"),
            PlayerActions.handle_quit_command,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^(Да, вывести \d+|Нет, отменить)$"),
            PlayerActions.handle_confirmation,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^(Да, завершить игру|Нет, продолжить играть)$"),
            GameManagement.handle_confirmation,
        )
    )
    application.add_handler(CommandHandler("startgame", GameManagement.start_game))
    application.add_handler(CommandHandler("buyin", PlayerActions.buyin))
    application.add_handler(CommandHandler("summary", PlayerActions.summary))
    application.add_handler(CommandHandler("summarygames", PlayerActions.summarygames))
    application.add_handler(CommandHandler("log", PlayerActions.log))
    application.add_handler(CommandHandler("help", PlayerActions.help))
    application.add_handler(CommandHandler("mystats", PlayerActions.stats))

    # Назначение функции инициализации после запуска
    application.post_init = post_init
    return application


def run_bot_blocking():
    """Запускает Telegram-бота в блокирующем режиме."""
    asyncio.set_event_loop(asyncio.new_event_loop())  # Обязательное условие в потоке
    app = build_application()
    app.run_polling(stop_signals=[])  # Отключаем работу сигналов в потоке

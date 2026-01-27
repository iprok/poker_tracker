import asyncio
from telegram.ext import Application, MessageHandler, filters
from telegram import BotCommandScopeChat, BotCommandScopeAllPrivateChats
from commands.game_management import GameManagement
from commands.player_actions import PlayerActions
from config import BOT_TOKEN, CHANNEL_ID


async def post_init(application: Application) -> None:
    """Настройка команд после запуска бота."""
    bot_info = await application.bot.get_me()
    bn = bot_info.username

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

    # Регистрация обработчиков
    application.add_handler(
        MessageHandler(filters.Regex(rf"^\s*/menu(@{bn})?$"), PlayerActions.show_menu)
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/close_menu(@{bn})?$"), PlayerActions.close_menu
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/quitgame(@{bn})?$"), PlayerActions.handle_quit_button
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/endgame(@{bn})?$"),
            GameManagement.handle_endgame_command,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/quit(@{bn})?( (0|\d{4,5}))?$"),
            PlayerActions.handle_quit_command,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^(Да, вывести (0|\d{4,5})|Нет, отменить)$"),
            PlayerActions.handle_confirmation,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^(Да, завершить игру|Нет, продолжить играть)$"),
            GameManagement.handle_confirmation,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/startgame(@{bn})?$"), GameManagement.start_game
        )
    )
    application.add_handler(
        MessageHandler(filters.Regex(rf"^\s*/buyin(@{bn})?$"), PlayerActions.buyin)
    )
    application.add_handler(
        MessageHandler(filters.Regex(rf"^\s*/summary(@{bn})?$"), PlayerActions.summary)
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/summarygames(@{bn})?$"), PlayerActions.summarygames
        )
    )
    application.add_handler(
        MessageHandler(filters.Regex(rf"^\s*/log(@{bn})?$"), PlayerActions.log)
    )
    application.add_handler(
        MessageHandler(filters.Regex(rf"^\s*/help(@{bn})?$"), PlayerActions.help)
    )
    application.add_handler(
        MessageHandler(filters.Regex(rf"^\s*/mystats(@{bn})?$"), PlayerActions.stats)
    )


def build_application() -> Application:
    """Создаёт и настраивает экземпляр Telegram Application."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Назначение функции инициализации после запуска
    application.post_init = post_init
    return application


def run_bot():
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    run_bot()

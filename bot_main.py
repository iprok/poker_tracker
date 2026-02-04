import asyncio
from telegram.ext import Application, MessageHandler, filters
from telegram import BotCommandScopeChat, BotCommandScopeAllPrivateChats
from commands.game_management import GameManagement
from commands.player_actions import PlayerActions
from commands.tournament_management import TournamentManagement
from config import BOT_TOKEN, CHANNEL_ID
from di_container import DIContainer
from engine import session, Session
from domain.repository.tournament_repository import TournamentRepository
from telegram import BotCommandScopeChat, BotCommandScopeAllPrivateChats
# Initialize database tables
from db_init import init_db

init_db()


async def setup_bot_commands(bot) -> None:
    """Sets bot commands based on the current state (e.g., active tournament)."""
    db_session = Session()
    try:
        has_active_tournament = (
            TournamentRepository(db_session).find_active_tournament() is not None
        )

        commands = [
            ("buyin", "Закуп"),
            ("quitgame", "Выйти"),
            ("menu", "Управление игрой"),
            ("mystats", "Ваша статистика"),
        ]

        if has_active_tournament:
            commands.extend(
                [
                    ("join_tournament", "Вступить в турнир"),
                    ("leave_tournament", "Покинуть турнир"),
                ]
            )

        await bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeAllPrivateChats(),
        )
    finally:
        db_session.close()


async def post_init(application: Application) -> None:
    """Настройка команд после запуска бота."""
    bot_info = await application.bot.get_me()
    bn = bot_info.username

    # Initialize DI container
    di_container = DIContainer(db_session=session)
    tournament_management = TournamentManagement(
        start_tournament_use_case=di_container.get_start_tournament_use_case(),
        end_tournament_use_case=di_container.get_end_tournament_use_case(),
        register_player_use_case=di_container.get_register_player_use_case(),
        eliminate_player_use_case=di_container.get_eliminate_player_use_case(),
        get_tournament_summary_use_case=di_container.get_tournament_summary_use_case(),
        shuffle_players_use_case=di_container.get_shuffle_players_use_case(),
        notification_public_tournament_channel_service=di_container.get_notification_public_tournament_channel_service(),
        notification_bot_channel_service=di_container.get_notification_bot_channel_service(),
    )

    try:
        await application.bot.set_my_commands(
            commands=[("menu", "Показать меню команд")],
            scope=BotCommandScopeChat(chat_id=CHANNEL_ID),
        )
    except Exception:
        await application.bot.delete_my_commands()

    # Initial setup of private commands
    await setup_bot_commands(application.bot)

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
            filters.Regex(rf"^\s*/quit(@{bn})?( (0|\d{{4,5}}))?$"),
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
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/start_tournament(@{bn})?$"),
            tournament_management.start_tournament,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/end_tournament(@{bn})?$"),
            tournament_management.end_tournament,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/join_tournament(@{bn})?$"),
            tournament_management.register_player,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/summary_tournament(@{bn})?$"),
            tournament_management.summary_tournament,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/shuffle_players(@{bn})?$"),
            tournament_management.shuffle_players,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(rf"^\s*/leave_tournament(@{bn})?$"),
            tournament_management.eliminate_player,
        )
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

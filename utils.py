from datetime import datetime, timezone
import pytz
from config import TIMEZONE
from telegram.ext import ContextTypes


def format_datetime(dt: datetime) -> str:
    """
    Форматирует дату и время в указанный временной пояс и возвращает строку формата DD-MM-YYYY HH:MM:SS.
    """
    return format_datetime_by_format(dt, "%d-%m-%Y %H:%M:%S")


def format_datetime_to_date(dt: datetime) -> str:
    """
    Форматирует дату и время в указанный временной пояс и возвращает строку формата DD-MM-YYYY.
    """
    return format_datetime_by_format(dt, "%d-%m-%Y")


def format_datetime_by_format(dt: datetime, format) -> str:
    timezone = pytz.timezone(TIMEZONE)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)  # Применяем UTC, если временная зона отсутствует
    return dt.astimezone(timezone).strftime(format)


async def get_user_info(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    try:
        # Получаем информацию о пользователе
        user = await context.bot.get_chat(user_id)

        # Формируем строку с именем и фамилией, если они есть
        if user.first_name or user.last_name:
            name_parts = []
            if user.first_name:
                name_parts.append(
                    user.first_name.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&apos;")
                    .replace("/", "&#47;")
                )
            if user.last_name:
                name_parts.append(
                    user.last_name.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&apos;")
                    .replace("/", "&#47;")
                )
            return " ".join(name_parts)

        # Если имя и фамилия отсутствуют, используем username
        if user.username:
            return f"@{user.username}"

        # Если username отсутствует, возвращаем None
        return None

    except Exception as e:
        # В случае ошибки возвращаем None
        print(f"Ошибка при получении информации о пользователе: {e}")
        return None


from engine import Session
from domain.repository.tournament_repository import TournamentRepository
from telegram import BotCommandScopeAllPrivateChats


def ensure_aware(dt: datetime) -> datetime:
    """
    Превращает offset-naive datetime в offset-aware с UTC, если требуется.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


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
                    ("out_tournament", "Покинуть турнир"),
                ]
            )

        await bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeAllPrivateChats(),
        )
    finally:
        db_session.close()

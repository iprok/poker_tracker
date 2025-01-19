from datetime import datetime, timezone
from domain.entity.game import Game
from domain.entity.player_action import PlayerAction
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import desc, or_
from sqlalchemy.sql import func
from engine import Session
from domain.repository.game_repository import GameRepository
from domain.repository.player_action_repository import PlayerActionRepository
from utils import format_datetime, format_datetime_to_date
from config import (
    CHIP_VALUE,
    CHIP_COUNT,
    USE_TABLE,
    SHOW_SUMMARY_ON_BUYIN,
    SHOW_SUMMARY_ON_QUIT,
    LOG_AMOUNT_LAST_GAMES,
)
from decorators import restrict_to_channel
from prettytable import PrettyTable


class PlayerActions:

    @staticmethod
    @restrict_to_channel
    async def buyin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game_id = context.bot_data.get("current_game_id")

        if current_game_id is None:
            await update.message.reply_text("Сначала начните игру командой /startgame.")
            session.close()
            return

        user = update.effective_user
        action = PlayerAction(
            game_id=current_game_id,
            user_id=user.id,
            username=user.username,
            action="buyin",
            chips=CHIP_COUNT,
            amount=CHIP_VALUE,
            timestamp=datetime.now(timezone.utc),
        )
        PlayerActionRepository(session).save(action)
        session.close()

        await update.message.reply_text(
            f"Закуп на {CHIP_COUNT} фишек ({CHIP_VALUE} лева) записан."
        )

        if SHOW_SUMMARY_ON_BUYIN:
            await PlayerActions.summary(update, context)

    @staticmethod
    @restrict_to_channel
    async def quit(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game_id = context.bot_data.get("current_game_id")

        if current_game_id is None:
            await update.message.reply_text("Сначала начните игру командой /startgame.")
            session.close()
            return

        total_buyins = (
            session.query(PlayerAction)
            .filter_by(game_id=current_game_id, action="buyin")
            .count()
            * CHIP_COUNT
        )

        total_quits = (
            session.query(PlayerAction)
            .filter_by(game_id=current_game_id, action="quit")
            .with_entities(func.sum(PlayerAction.chips))
            .scalar()
            or 0
        )

        max_chips = total_buyins - total_quits

        try:
            if not context.args:
                raise ValueError("Вы не указали количество фишек. Пример: /quit 1500")

            chips_left = int(context.args[0])
            if chips_left < 0:
                raise ValueError("Количество фишек не может быть меньше 0.")
            if chips_left > max_chips:
                raise ValueError(
                    f"Количество фишек не может быть больше доступных в банке: {max_chips}."
                )
        except (ValueError, IndexError) as e:
            await update.message.reply_text(f"Ошибка: {e}")
            session.close()
            return

        amount = (chips_left / CHIP_COUNT) * CHIP_VALUE
        user = update.effective_user
        action = PlayerAction(
            game_id=current_game_id,
            user_id=user.id,
            username=user.username,
            action="quit",
            chips=chips_left,
            amount=amount,
            timestamp=datetime.now(timezone.utc),
        )
        PlayerActionRepository(session).save(action)
        session.close()

        await update.message.reply_text(
            f"Выход записан. У вас осталось {chips_left} фишек, что эквивалентно {amount:.2f} лева."
        )

        if SHOW_SUMMARY_ON_QUIT:
            await PlayerActions.summary(update, context)

    @staticmethod
    @restrict_to_channel
    async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        actions = session.query(PlayerAction).all()
        log_text = "Лог действий:\n"
        for action in actions:
            formatted_timestamp = format_datetime(action.timestamp)
            amount = f"{action.amount:.2f}" if action.amount is not None else "None"
            log_text += f"{formatted_timestamp}: {action.username} - {action.action} ({action.chips} фишек, {amount} лева)\n"
        session.close()
        await update.message.reply_text(log_text)

    @staticmethod
    @restrict_to_channel
    async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        current_game_id = context.bot_data.get("current_game_id")
        if current_game_id is None:
            await update.message.reply_text("Игра не начата.")
            session.close()
            return

        game = session.query(Game).filter_by(id=current_game_id).one()
        actions = PlayerActionRepository(session).find_actions_by_game(game.id)
        summary_text = PlayerActions.summary_formatter(actions, game)

        await update.message.reply_text(summary_text, parse_mode="HTML")

        session.close()

    @staticmethod
    @restrict_to_channel
    async def summarygames(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session = Session()
        games = GameRepository(session).get_games_by_limit(LOG_AMOUNT_LAST_GAMES)

        summary_text = f"<pre>Сводка последних {LOG_AMOUNT_LAST_GAMES} игр</pre>"
        for game in games:
            actions = PlayerActionRepository(session).find_actions_by_game(game.id)
            summary_text += PlayerActions.summary_formatter(actions, game)

        await update.message.reply_text(summary_text, parse_mode="HTML")
        session.close()

    @staticmethod
    @restrict_to_channel
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "Список команд:\n"
            "/summary - Показать сводку текущей игры.\n"
            "/summarygames - Показать сводку последних игр.\n"
            "/log - Показать лог всех действий.\n"
            "/quit <фишки> - Выйти из игры, указав количество оставшихся фишек.\n"
            "/help - Показать это сообщение.\n\n"
            "/startgame - Начать новую игру.\n\n"
            "/buyin - Закупить фишки.\n\n"
            "/endgame - Завершить текущую игру.\n"
        )
        await update.message.reply_text(help_text)

    def summary_formatter(actions, game) -> str:
        player_stats = {}
        total_buyin = 0
        total_quit = 0

        summary_text = (
            f"\nСводка закупов за {format_datetime_to_date(game.start_time)}:\n"
        )

        if not actions:
            summary_text += f"Закупов в текущей игре ещё не было.\n"
            return summary_text

        for action in actions:
            if action.username not in player_stats:
                player_stats[action.username] = {"buyin": 0, "quit": 0}

            if action.action == "buyin":
                player_stats[action.username]["buyin"] += action.amount
                total_buyin += action.amount

            elif action.action == "quit":
                player_stats[action.username]["quit"] += action.amount
                total_quit += action.amount

        total_balance = total_buyin - total_quit

        if USE_TABLE:
            table = PrettyTable()
            table.field_names = ["Имя", "buy", "quit", "diff"]

            for username, stats in player_stats.items():
                balance = stats["quit"] - stats["buyin"]
                table.add_row(
                    [
                        username,
                        f"{stats['buyin']:.2f}",
                        f"{stats['quit']:.2f}",
                        f"{balance:.2f}",
                    ]
                )

            summary_text += f"<pre>{table}</pre>"
            return summary_text
        else:
            for username, stats in player_stats.items():
                balance = stats["quit"] - stats["buyin"]
                summary_text += (
                    f"{username}: закупился на {stats['buyin']:.2f} лева, "
                    f"вышел на {stats['quit']:.2f} лева, разница: {balance:.2f} лева\n"
                )
            summary_text += (
                f"\nОбщее количество денег в банке: {total_balance:.2f} лева.\n"
            )

            return summary_text
